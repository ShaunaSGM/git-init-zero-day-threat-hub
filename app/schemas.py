"""
Pydantic models for data validation, serialization, and API contracts.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from app.models import SeverityLevel, IndicatorType
import re


class IndicatorCreate(BaseModel):
    """Schema for creating a new threat indicator."""
    indicator_type: IndicatorType
    value: str = Field(..., min_length=1, max_length=1024)
    description: Optional[str] = None
    
    @field_validator("value")
    @classmethod
    def validate_indicator_value(cls, v: str, info):
        """Validate indicator value based on its type."""
        indicator_type = info.data.get("indicator_type")
        
        if indicator_type == IndicatorType.SHA256:
            # SHA256 must be 64 hexadecimal characters
            if not re.match(r"^[a-fA-F0-9]{64}$", v):
                raise ValueError("SHA256 must be a 64-character hexadecimal string")
        
        elif indicator_type == IndicatorType.IP_ADDRESS:
            # Simple IPv4/IPv6 validation
            ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
            ipv6_pattern = r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
            if not (re.match(ipv4_pattern, v) or re.match(ipv6_pattern, v)):
                raise ValueError("Invalid IP address format")
        
        elif indicator_type == IndicatorType.DOMAIN:
            # Basic domain validation
            domain_pattern = r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
            if not re.match(domain_pattern, v, re.IGNORECASE):
                raise ValueError("Invalid domain format")
        
        return v


class IndicatorResponse(BaseModel):
    """Schema for returning threat indicator data."""
    id: int
    advisory_id: int
    indicator_type: IndicatorType
    value: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ThreatAdvisoryCreate(BaseModel):
    """Schema for creating a new threat advisory."""
    title: str = Field(..., min_length=1, max_length=255)
    cve_id: Optional[str] = Field(None, max_length=50)
    threat_actor: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.MEDIUM
    indicators: List[IndicatorCreate] = Field(default_factory=list)


class ThreatAdvisoryResponse(BaseModel):
    """Schema for returning threat advisory data."""
    id: int
    title: str
    cve_id: Optional[str]
    threat_actor: Optional[str]
    description: Optional[str]
    severity: SeverityLevel
    published_at: datetime
    updated_at: datetime
    indicators: List[IndicatorResponse] = []
    
    class Config:
        from_attributes = True


class MatchRequest(BaseModel):
    """Schema for log matching requests."""
    log_data: str = Field(..., min_length=1, description="Raw log text or CSV data to match against IOCs")
    source_name: Optional[str] = Field(None, description="Name of the log source for audit purposes")


class MatchResult(BaseModel):
    """Schema for individual match results."""
    advisory_id: int
    advisory_title: str
    indicator_id: int
    indicator_type: IndicatorType
    matched_value: str
    severity: SeverityLevel
    threat_actor: Optional[str]


class MatchResponse(BaseModel):
    """Schema for returning match results."""
    total_matches: int
    matches: List[MatchResult]
    source_name: Optional[str]
    matched_at: datetime


class IndicatorSearchParams(BaseModel):
    """Schema for filtering indicators."""
    indicator_type: Optional[IndicatorType] = None
    severity: Optional[SeverityLevel] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
