"""
Core threat matching engine for correlating logs against indicators of compromise (IOCs).
"""
import re
import csv
import io
from typing import List, Tuple, Dict, Set
from sqlalchemy.orm import Session
from app import models
from app.schemas import MatchResult
from datetime import datetime


class ThreatMatcher:
    """Core matching algorithm for logs vs IOCs."""
    
    # Regex patterns for extracting indicators
    IPV4_PATTERN = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
    SHA256_PATTERN = re.compile(r'\b[a-fA-F0-9]{64}\b')
    DOMAIN_PATTERN = re.compile(r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b', re.IGNORECASE)
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    def __init__(self, db: Session):
        """Initialize matcher with database session."""
        self.db = db
    
    def extract_indicators(self, log_data: str) -> Dict[models.IndicatorType, Set[str]]:
        """
        Extract potential indicators from raw log text.
        
        Args:
            log_data: Raw log text to scan
            
        Returns:
            Dictionary mapping indicator types to sets of extracted values
        """
        extracted = {
            models.IndicatorType.IP_ADDRESS: set(self.IPV4_PATTERN.findall(log_data)),
            models.IndicatorType.SHA256: set(self.SHA256_PATTERN.findall(log_data)),
            models.IndicatorType.DOMAIN: set(self.DOMAIN_PATTERN.findall(log_data)),
            models.IndicatorType.EMAIL: set(self.EMAIL_PATTERN.findall(log_data)),
        }
        return extracted
    
    def parse_csv_logs(self, csv_data: str) -> List[Dict[str, str]]:
        """
        Parse CSV-formatted log data.
        
        Args:
            csv_data: CSV-formatted string
            
        Returns:
            List of dictionaries representing CSV rows
        """
        logs = []
        try:
            reader = csv.DictReader(io.StringIO(csv_data))
            for row in reader:
                if row:
                    logs.append(row)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
        return logs
    
    def match_indicators(self, extracted: Dict[models.IndicatorType, Set[str]]) -> List[models.Indicator]:
        """
        Query database for indicators matching extracted values using IN clauses.
        Bulk query for performance optimization.
        
        Args:
            extracted: Dictionary of extracted indicator types and values
            
        Returns:
            List of matching Indicator objects from database
        """
        matched_indicators = []
        
        for indicator_type, values in extracted.items():
            if not values:
                continue
            
            # Bulk query using IN clause
            indicators = self.db.query(models.Indicator).filter(
                models.Indicator.indicator_type == indicator_type,
                models.Indicator.value.in_(list(values))
            ).all()
            
            matched_indicators.extend(indicators)
        
        return matched_indicators
    
    def generate_match_results(
        self,
        matched_indicators: List[models.Indicator],
        source_log: str
    ) -> List[MatchResult]:
        """
        Generate match results from matched indicators.
        
        Args:
            matched_indicators: List of matched Indicator objects
            source_log: Original log data (for audit)
            
        Returns:
            List of MatchResult objects
        """
        results = []
        
        for indicator in matched_indicators:
            result = MatchResult(
                advisory_id=indicator.advisory_id,
                advisory_title=indicator.advisory.title,
                indicator_id=indicator.id,
                indicator_type=indicator.indicator_type,
                matched_value=indicator.value,
                severity=indicator.advisory.severity,
                threat_actor=indicator.advisory.threat_actor
            )
            results.append(result)
            
            # Log to audit table
            audit_log = models.MatchAudit(
                advisory_id=indicator.advisory_id,
                matched_indicator_id=indicator.id,
                matched_value=indicator.value,
                source_log=source_log[:500],  # Truncate for storage
                severity=indicator.advisory.severity,
                matched_at=datetime.utcnow()
            )
            self.db.add(audit_log)
        
        self.db.commit()
        return results
    
    def match_logs(
        self,
        log_data: str,
        is_csv: bool = False
    ) -> Tuple[List[MatchResult], int]:
        """
        Main matching workflow: extract, query, and return results.
        
        Args:
            log_data: Raw log text or CSV data
            is_csv: Whether input is CSV formatted
            
        Returns:
            Tuple of (match results, total matches count)
        """
        if is_csv:
            csv_logs = self.parse_csv_logs(log_data)
            # Combine all CSV rows into searchable text
            combined_text = ' '.join(' '.join(str(v) for v in row.values()) for row in csv_logs)
        else:
            combined_text = log_data
        
        # Extract indicators from logs
        extracted = self.extract_indicators(combined_text)
        
        # Query database for matches
        matched_indicators = self.match_indicators(extracted)
        
        # Generate results and audit logs
        results = self.generate_match_results(matched_indicators, combined_text)
        
        return results, len(results)
