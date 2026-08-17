# Staging Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Zero-Day Threat Hub to a staging environment using Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git
- Bash shell
- 4GB+ RAM
- 10GB+ disk space

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/ShaunaSGM/git-init-zero-day-threat-hub.git
cd git-init-zero-day-threat-hub
git checkout setup/phase-1-foundation
```

### 2. Run Deployment Script

```bash
chmod +x scripts/deploy-staging.sh
./scripts/deploy-staging.sh
```

The script will:
- ✅ Check Docker prerequisites
- ✅ Create `.env` configuration
- ✅ Generate self-signed SSL certificates
- ✅ Build Docker images
- ✅ Start all containers (API, PostgreSQL, Nginx)
- ✅ Wait for services to become healthy
- ✅ Initialize the database
- ✅ Run unit tests
- ✅ Display deployment summary

### 3. Access the Application

**API Documentation:**
- Swagger UI: http://localhost/docs
- ReDoc: http://localhost/redoc

**Health Check:**
- http://localhost/health

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)             │
│  - Port 80 (redirects to 443)                       │
│  - Port 443 (SSL/TLS)                               │
│  - Load balancing                                    │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│              FastAPI Application                     │
│  - Port 8000                                        │
│  - Uvicorn ASGI server                              │
│  - Hot-reload enabled (for development)             │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│              PostgreSQL Database                     │
│  - Port 5432                                        │
│  - Persistent volume storage                        │
│  - Health checks enabled                            │
└─────────────────────────────────────────────────────┘
```

## Docker Compose Services

### api (FastAPI)
```yaml
Container: threat_hub_api
Port: 8000
Environment: DATABASE_URL, DEBUG
Volumes: ./:/app (live code reload)
Health Check: curl http://localhost:8000/health
```

### postgres (Database)
```yaml
Container: threat_hub_postgres
Port: 5432
Image: postgres:15-alpine
Database: threat_hub
User: threat_admin
Volume: postgres_data (persistent)
Health Check: pg_isready
```

### nginx (Reverse Proxy)
```yaml
Container: threat_hub_nginx
Port: 80, 443
SSL Certificates: ./ssl/cert.pem, ./ssl/key.pem
Features:
  - GZIP compression
  - Security headers
  - TLS 1.2+
```

## Configuration

### Environment Variables (.env)

Create `.env` file from template:
```bash
cp .env.staging.example .env
```

**Key variables to update:**
```
DATABASE_URL=postgresql://threat_admin:PASSWORD@postgres:5432/threat_hub
DB_PASSWORD=secure_password_here
DEBUG=False
SECRET_KEY=your_secret_key_here
```

### SSL Certificates

Self-signed certificates are generated automatically. For production:

1. Obtain valid certificates (Let's Encrypt, etc.)
2. Place `cert.pem` and `key.pem` in `./ssl/` directory
3. Update `nginx.conf` if certificate paths differ

Generate new self-signed certificate:
```bash
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
```

## Common Commands

### View Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f nginx
```

### Execute Commands in Container
```bash
# Run shell in API container
docker-compose exec api bash

# Run Python commands
docker-compose exec api python -c "..."

# Run pytest
docker-compose exec api pytest tests/ -v
```

### Stop Services
```bash
docker-compose stop
```

### Restart Services
```bash
docker-compose restart
```

### Remove All Services and Volumes
```bash
docker-compose down -v
```

## Testing the Deployment

### 1. Health Check
```bash
curl http://localhost/health
# Expected: {"status": "healthy", "service": "Zero-Day Threat Hub"}
```

### 2. Create Advisory
```bash
curl -X POST "http://localhost/advisories/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "CVE-2024-0001 Test Advisory",
    "cve_id": "CVE-2024-0001",
    "threat_actor": "APT-Test",
    "severity": "Critical",
    "indicators": [
      {
        "indicator_type": "IP_Address",
        "value": "192.168.1.100",
        "description": "Test C2 server"
      },
      {
        "indicator_type": "SHA256",
        "value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "description": "Test hash"
      }
    ]
  }'
```

### 3. List Advisories
```bash
curl http://localhost/advisories/
```

### 4. Match Logs
```bash
curl -X POST "http://localhost/match/" \
  -H "Content-Type: application/json" \
  -d '{
    "log_data": "Connection from 192.168.1.100 detected at 10:30:00",
    "source_name": "firewall_test"
  }'
```

### 5. Run Tests
```bash
docker-compose exec api pytest tests/test_matcher.py -v
```

## Monitoring

### Container Health
```bash
docker-compose ps
# Look for "healthy" status
```

### Application Logs
```bash
docker-compose logs --tail=100 api
```

### Database Logs
```bash
docker-compose logs --tail=50 postgres
```

### Nginx Access Logs
```bash
docker-compose logs nginx
```

## Troubleshooting

### API Container Not Starting
```bash
docker-compose logs api
# Check DATABASE_URL and credentials in .env
```

### Database Connection Failed
```bash
docker-compose logs postgres
# Ensure postgres service is healthy
docker-compose ps
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml
# Or stop conflicting services
lsof -i :80
lsof -i :443
lsof -i :5432
```

### SSL Certificate Issues
```bash
# Regenerate self-signed certificates
rm ssl/*
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
docker-compose restart nginx
```

### Tests Failing
```bash
docker-compose exec api pytest tests/ -v
# Check test output for specific failures
```

## Performance Optimization

### Database Connections
Adjust in `config.py`:
```python
# Connection pooling
pool_size = 20
max_overflow = 40
```

### Nginx Worker Processes
Edit `nginx.conf`:
```nginx
worker_processes auto;  # Uses all CPU cores
worker_connections 2048;
```

### Application Instances
Scale API in `docker-compose.yml`:
```bash
docker-compose up -d --scale api=3
```

## Security Considerations

### For Staging
- Use self-signed SSL certificates ✅ (automatic)
- Default PostgreSQL credentials (change them!)
- Debug mode disabled ✅

### Before Production
- [ ] Replace self-signed certificates with valid ones
- [ ] Change all default passwords
- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure firewall rules
- [ ] Set up backup strategy
- [ ] Enable audit logging
- [ ] Configure rate limiting
- [ ] Set up monitoring/alerting

## Cleanup

Remove the entire staging deployment:
```bash
chmod +x scripts/cleanup-staging.sh
./scripts/cleanup-staging.sh
```

Or manually:
```bash
docker-compose down -v
rm -rf ssl/
rm .env
```

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Nginx Documentation](https://nginx.org/en/docs/)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review container logs
3. Check Docker Compose status
4. Review application health endpoints

---

**Deployment Date**: 2026-08-17  
**Environment**: Staging  
**Version**: 1.0.0
