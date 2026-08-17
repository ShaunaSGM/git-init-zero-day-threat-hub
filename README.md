# Zero-Day Threat Hub

A threat intelligence and detection matching system for identifying and correlating zero-day exploits and indicators of compromise (IOCs) against enterprise logs.

## Features

- **Threat Advisory Management**: Publish and track zero-day advisories with associated metadata (CVE, threat actor, severity)
- **Indicator Management**: Store and query various types of IOCs (IP addresses, file hashes, domains, YARA rules)
- **Log Matching Engine**: Real-time correlation of enterprise logs against threat indicators using regex extraction and bulk database queries
- **Audit Logging**: Complete history of all matches for compliance and forensic analysis
- **FastAPI REST API**: Modern async endpoints for all operations
- **SQLAlchemy ORM**: Flexible database support (SQLite for dev, PostgreSQL for production)
- **Pydantic Validation**: Strict input validation with type checking

## Architecture

```
zero-day-threat-hub/
├── .gitignore
├── README.md
├── requirements.txt           # Project dependencies
├── config.py                  # Environment and database configuration
├── app/
│   ├── __init__.py
│   ├── database.py           # SQLAlchemy engine and sessions
│   ├── models.py             # ORM models (ThreatAdvisory, Indicator, MatchAudit)
│   ├── schemas.py            # Pydantic validation models
│   ├── matcher.py            # Core matching algorithm
│   └── main.py               # FastAPI routes and endpoints
├── tests/
│   └── test_matcher.py       # Unit tests for matching logic
└── sample_data/
    ├── sample_threats.json   # Example threat advisories
    └── test_logs.csv         # Sample enterprise logs
```

## Installation

### Prerequisites
- Python 3.10+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ShaunaSGM/git-init-zero-day-threat-hub.git
cd git-init-zero-day-threat-hub
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:
```env
DATABASE_URL=sqlite:///./threat_hub.db
DEBUG=False
```

For PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@localhost/threat_hub
```

## Running the Application

### Start the API server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Health Check
```
GET /health
```

### Threat Advisories
```
POST /advisories/              # Create new advisory with IOCs
GET /advisories/               # List all advisories (with severity filtering)
GET /advisories/{advisory_id}  # Get specific advisory
```

### Indicators
```
GET /indicators/               # Search/filter IOCs by type, value, etc.
```

### Log Matching
```
POST /match/                   # Upload logs to check against IOC database
```

## Example Usage

### Create a Threat Advisory
```bash
curl -X POST "http://localhost:8000/advisories/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "CVE-2024-1234 RCE",
    "cve_id": "CVE-2024-1234",
    "threat_actor": "APT-28",
    "severity": "Critical",
    "indicators": [
      {"indicator_type": "IP_Address", "value": "192.168.1.100"},
      {"indicator_type": "SHA256", "value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
    ]
  }'
```

### Match Logs
```bash
curl -X POST "http://localhost:8000/match/" \
  -H "Content-Type: application/json" \
  -d '{
    "log_data": "Connection from 192.168.1.100 detected at 10:30:00",
    "source_name": "firewall_log_2024_01_15"
  }'
```

## Running Tests

```bash
pytest tests/test_matcher.py -v
```

For coverage report:
```bash
pytest tests/ --cov=app --cov-report=html
```

## Database Schema

### ThreatAdvisory
- `id`: Primary key
- `title`: Advisory title
- `cve_id`: Unique CVE identifier
- `threat_actor`: Name of threat actor
- `description`: Detailed description
- `severity`: Critical, High, Medium, Low
- `published_at`, `updated_at`: Timestamps

### Indicator
- `id`: Primary key
- `advisory_id`: Foreign key to ThreatAdvisory
- `indicator_type`: IP_Address, SHA256, YARA_Rule, Domain, Email
- `value`: The IOC value (IP, hash, domain, etc.)
- `description`: Details about this indicator
- `created_at`: Timestamp

### MatchAudit
- `id`: Primary key
- `advisory_id`: Foreign key to ThreatAdvisory
- `matched_indicator_id`: Foreign key to Indicator
- `matched_value`: The value that matched
- `source_log`: Truncated source log text (for audit)
- `severity`: Severity level
- `matched_at`: Timestamp of match
- `notes`: Additional notes

## Matching Engine

The `ThreatMatcher` class provides:

1. **Indicator Extraction**: Uses regex patterns to extract potential IOCs from logs
   - IPv4 addresses
   - SHA256 hashes
   - Domains
   - Email addresses

2. **Bulk Matching**: Queries database using SQL IN clauses for performance

3. **Result Generation**: Creates audit logs for compliance and forensics

## Project Phases

- **Phase 1**: Project Foundation (✓ Complete)
  - Environment setup, database layer, schemas
  
- **Phase 2**: SQL Competency (✓ Complete)
  - Database models and relationships
  
- **Phase 3**: Python Logic (✓ Complete)
  - Matching engine with regex extraction
  
- **Phase 4**: API & Testing (✓ Complete)
  - FastAPI endpoints and pytest unit tests

## License

MIT

## Author

ShaunaSGM
