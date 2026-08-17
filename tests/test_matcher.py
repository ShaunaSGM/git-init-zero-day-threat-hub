"""
Unit tests for the threat matching engine.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.database import Base
from app.models import (
    ThreatAdvisory,
    Indicator,
    IndicatorType,
    SeverityLevel,
    MatchAudit
)
from app.matcher import ThreatMatcher


# Setup test database
@pytest.fixture
def test_db():
    """Create an in-memory SQLite test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()


@pytest.fixture
def sample_advisory(test_db):
    """Create a sample threat advisory for testing."""
    advisory = ThreatAdvisory(
        title="CVE-2024-1234 Remote Code Execution",
        cve_id="CVE-2024-1234",
        threat_actor="APT-28",
        description="Critical RCE vulnerability in Apache WebServer",
        severity=SeverityLevel.CRITICAL
    )
    
    # Add indicators
    indicators = [
        Indicator(
            indicator_type=IndicatorType.IP_ADDRESS,
            value="192.168.1.100",
            description="C2 Server IP"
        ),
        Indicator(
            indicator_type=IndicatorType.SHA256,
            value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            description="Malware hash"
        ),
        Indicator(
            indicator_type=IndicatorType.DOMAIN,
            value="evil.com",
            description="Command & Control Domain"
        )
    ]
    
    for ind in indicators:
        advisory.indicators.append(ind)
    
    test_db.add(advisory)
    test_db.commit()
    return advisory


class TestThreatMatcher:
    """Test suite for ThreatMatcher class."""
    
    def test_ipv4_extraction(self, test_db, sample_advisory):
        """Test IPv4 address extraction from logs."""
        matcher = ThreatMatcher(test_db)
        log = "Connection from 192.168.1.100 detected at 10:30:00"
        
        extracted = matcher.extract_indicators(log)
        
        assert IndicatorType.IP_ADDRESS in extracted
        assert "192.168.1.100" in extracted[IndicatorType.IP_ADDRESS]
    
    def test_sha256_extraction(self, test_db, sample_advisory):
        """Test SHA256 hash extraction from logs."""
        matcher = ThreatMatcher(test_db)
        log = f"File hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        
        extracted = matcher.extract_indicators(log)
        
        assert IndicatorType.SHA256 in extracted
        assert "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" in extracted[IndicatorType.SHA256]
    
    def test_domain_extraction(self, test_db, sample_advisory):
        """Test domain extraction from logs."""
        matcher = ThreatMatcher(test_db)
        log = "DNS query to evil.com blocked"
        
        extracted = matcher.extract_indicators(log)
        
        assert IndicatorType.DOMAIN in extracted
        assert "evil.com" in extracted[IndicatorType.DOMAIN]
    
    def test_match_indicators(self, test_db, sample_advisory):
        """Test matching extracted indicators against database."""
        matcher = ThreatMatcher(test_db)
        
        extracted = {
            IndicatorType.IP_ADDRESS: {"192.168.1.100"},
            IndicatorType.SHA256: set(),
            IndicatorType.DOMAIN: set(),
            IndicatorType.EMAIL: set()
        }
        
        matched = matcher.match_indicators(extracted)
        
        assert len(matched) == 1
        assert matched[0].value == "192.168.1.100"
    
    def test_match_logs_integration(self, test_db, sample_advisory):
        """Test end-to-end log matching workflow."""
        matcher = ThreatMatcher(test_db)
        log = "Connection from 192.168.1.100 on 2024-01-15"
        
        results, total = matcher.match_logs(log)
        
        assert total == 1
        assert results[0].matched_value == "192.168.1.100"
        assert results[0].severity == SeverityLevel.CRITICAL
        assert results[0].threat_actor == "APT-28"
    
    def test_no_matches(self, test_db, sample_advisory):
        """Test behavior when no indicators match."""
        matcher = ThreatMatcher(test_db)
        log = "Normal system activity detected"
        
        results, total = matcher.match_logs(log)
        
        assert total == 0
        assert len(results) == 0
    
    def test_audit_logging(self, test_db, sample_advisory):
        """Test that matches are logged in audit table."""
        matcher = ThreatMatcher(test_db)
        log = "Connection from 192.168.1.100 detected"
        
        results, total = matcher.match_logs(log)
        
        audit_logs = test_db.query(MatchAudit).all()
        assert len(audit_logs) == 1
        assert audit_logs[0].matched_value == "192.168.1.100"
        assert audit_logs[0].severity == SeverityLevel.CRITICAL
    
    def test_csv_parsing(self, test_db):
        """Test CSV log parsing."""
        matcher = ThreatMatcher(test_db)
        csv_data = "ip,timestamp,event\n192.168.1.100,2024-01-15 10:30:00,connection"
        
        logs = matcher.parse_csv_logs(csv_data)
        
        assert len(logs) == 1
        assert logs[0]["ip"] == "192.168.1.100"
    
    def test_csv_parsing_invalid(self, test_db):
        """Test CSV parsing with invalid data."""
        matcher = ThreatMatcher(test_db)
        
        with pytest.raises(ValueError):
            matcher.parse_csv_logs("invalid\x00data")
    
    def test_multiple_matches(self, test_db, sample_advisory):
        """Test matching multiple indicators in single log."""
        matcher = ThreatMatcher(test_db)
        log = "Connection from 192.168.1.100 to evil.com with file e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        
        results, total = matcher.match_logs(log)
        
        assert total == 3
        assert len(results) == 3
