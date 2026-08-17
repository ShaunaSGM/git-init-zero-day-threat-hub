"""
FastAPI main application with threat intelligence endpoints.
"""
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from config import settings
from app.database import get_db, init_db
from app.models import ThreatAdvisory, Indicator, IndicatorType, SeverityLevel
from app.schemas import (
    ThreatAdvisoryCreate,
    ThreatAdvisoryResponse,
    IndicatorResponse,
    MatchRequest,
    MatchResponse,
    MatchResult,
    IndicatorSearchParams
)
from app.matcher import ThreatMatcher

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Zero-Day Threat Hub: Threat Intelligence and Detection Matching System"
)


# Startup event
@app.on_event("startup")
def startup():
    """Initialize database on startup."""
    init_db()


# Health check
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


# ============================================================================
# ADVISORY ENDPOINTS
# ============================================================================

@app.post("/advisories/", response_model=ThreatAdvisoryResponse, status_code=201)
def create_advisory(
    advisory: ThreatAdvisoryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new zero-day threat advisory with associated indicators.
    
    - **title**: Advisory title (required)
    - **cve_id**: CVE identifier (optional)
    - **threat_actor**: Name of threat actor (optional)
    - **description**: Detailed description (optional)
    - **severity**: Threat severity level
    - **indicators**: List of IOCs to associate with advisory
    """
    # Check for duplicate CVE
    if advisory.cve_id:
        existing = db.query(ThreatAdvisory).filter(
            ThreatAdvisory.cve_id == advisory.cve_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Advisory with this CVE ID already exists")
    
    # Create advisory
    db_advisory = ThreatAdvisory(
        title=advisory.title,
        cve_id=advisory.cve_id,
        threat_actor=advisory.threat_actor,
        description=advisory.description,
        severity=advisory.severity
    )
    
    # Add indicators
    for ind in advisory.indicators:
        db_indicator = Indicator(
            indicator_type=ind.indicator_type,
            value=ind.value,
            description=ind.description
        )
        db_advisory.indicators.append(db_indicator)
    
    db.add(db_advisory)
    db.commit()
    db.refresh(db_advisory)
    
    return db_advisory


@app.get("/advisories/", response_model=List[ThreatAdvisoryResponse])
def list_advisories(
    severity: Optional[SeverityLevel] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List all threat advisories with optional filtering.
    """
    query = db.query(ThreatAdvisory)
    
    if severity:
        query = query.filter(ThreatAdvisory.severity == severity)
    
    advisories = query.offset(offset).limit(limit).all()
    return advisories


@app.get("/advisories/{advisory_id}", response_model=ThreatAdvisoryResponse)
def get_advisory(
    advisory_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific advisory by ID.
    """
    advisory = db.query(ThreatAdvisory).filter(
        ThreatAdvisory.id == advisory_id
    ).first()
    
    if not advisory:
        raise HTTPException(status_code=404, detail="Advisory not found")
    
    return advisory


# ============================================================================
# INDICATOR ENDPOINTS
# ============================================================================

@app.get("/indicators/", response_model=List[IndicatorResponse])
def search_indicators(
    indicator_type: Optional[IndicatorType] = None,
    value: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Search and filter stored indicators of compromise.
    """
    query = db.query(Indicator)
    
    if indicator_type:
        query = query.filter(Indicator.indicator_type == indicator_type)
    
    if value:
        query = query.filter(Indicator.value.ilike(f"%{value}%"))
    
    indicators = query.offset(offset).limit(limit).all()
    return indicators


# ============================================================================
# MATCHING ENDPOINTS
# ============================================================================

@app.post("/match/", response_model=MatchResponse, status_code=200)
def match_logs(
    request: MatchRequest,
    db: Session = Depends(get_db)
):
    """
    Upload enterprise logs to check against threat database IOCs.
    
    - **log_data**: Raw log text or CSV data to analyze (required)
    - **source_name**: Name of log source for audit purposes (optional)
    """
    matcher = ThreatMatcher(db)
    
    # Detect if input is CSV (basic heuristic)
    is_csv = request.log_data.strip().startswith((',', '"')) or '\n' in request.log_data and ',' in request.log_data.split('\n')[0]
    
    try:
        matches, total = matcher.match_logs(request.log_data, is_csv=is_csv)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return MatchResponse(
        total_matches=total,
        matches=matches,
        source_name=request.source_name,
        matched_at=datetime.utcnow()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
