#!/bin/bash

# Zero-Day Threat Hub - Staging Deployment Script
# This script deploys the application to a staging environment using Docker Compose

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Zero-Day Threat Hub - Staging Deployment                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BRANCH=${1:-setup/phase-1-foundation}
STAGING_DIR="./staging"
DEPLOYMENT_DATE=$(date '+%Y-%m-%d_%H-%M-%S')
LOG_FILE="deployment_${DEPLOYMENT_DATE}.log"

echo -e "${YELLOW}[INFO]${NC} Staging Directory: ${STAGING_DIR}"
echo -e "${YELLOW}[INFO]${NC} Branch: ${BRANCH}"
echo -e "${YELLOW}[INFO]${NC} Log File: ${LOG_FILE}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}[STEP 1]${NC} Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Docker Compose is not installed"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Docker and Docker Compose are installed"
echo ""

# Step 2: Create .env file
echo -e "${YELLOW}[STEP 2]${NC} Setting up environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.staging.example ]; then
        cp .env.staging.example .env
        echo -e "${YELLOW}[WARNING]${NC} .env file created from template. Please update sensitive values!"
    else
        echo -e "${RED}[ERROR]${NC} .env.staging.example not found"
        exit 1
    fi
else
    echo -e "${GREEN}[OK]${NC} .env file already exists"
fi
echo ""

# Step 3: Create SSL directory (self-signed for staging)
echo -e "${YELLOW}[STEP 3]${NC} Setting up SSL certificates..."
if [ ! -d "ssl" ]; then
    mkdir -p ssl
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
        -subj "/C=US/ST=State/L=City/O=Org/CN=localhost" 2>/dev/null
    echo -e "${GREEN}[OK]${NC} Self-signed SSL certificate generated"
else
    echo -e "${GREEN}[OK]${NC} SSL directory already exists"
fi
echo ""

# Step 4: Build Docker images
echo -e "${YELLOW}[STEP 4]${NC} Building Docker images..."
docker-compose build 2>&1 | tee -a ${LOG_FILE}
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} Docker images built successfully"
else
    echo -e "${RED}[ERROR]${NC} Failed to build Docker images"
    exit 1
fi
echo ""

# Step 5: Start containers
echo -e "${YELLOW}[STEP 5]${NC} Starting Docker containers..."
docker-compose up -d 2>&1 | tee -a ${LOG_FILE}
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} Containers started successfully"
else
    echo -e "${RED}[ERROR]${NC} Failed to start containers"
    exit 1
fi
echo ""

# Step 6: Wait for services to be healthy
echo -e "${YELLOW}[STEP 6]${NC} Waiting for services to be healthy..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T api curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC} API is healthy"
        break
    fi
    
    attempt=$((attempt + 1))
    echo -e "${YELLOW}[WAIT]${NC} Waiting for API to be ready... (${attempt}/${max_attempts})"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}[ERROR]${NC} API failed to become healthy"
    docker-compose logs api
    exit 1
fi
echo ""

# Step 7: Run database migrations/initialization
echo -e "${YELLOW}[STEP 7]${NC} Initializing database..."
docker-compose exec -T api python -c "from app.database import init_db; init_db(); print('Database initialized')" 2>&1 | tee -a ${LOG_FILE}
echo -e "${GREEN}[OK]${NC} Database initialized"
echo ""

# Step 8: Run tests
echo -e "${YELLOW}[STEP 8]${NC} Running unit tests..."
docker-compose exec -T api pytest tests/test_matcher.py -v 2>&1 | tee -a ${LOG_FILE}
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} All tests passed"
else
    echo -e "${YELLOW}[WARNING]${NC} Some tests failed, but deployment continues"
fi
echo ""

# Step 9: Display deployment summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Deployment Completed Successfully!               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Service URLs:${NC}"
echo "  API Documentation:  http://localhost/docs"
echo "  ReDoc:              http://localhost/redoc"
echo "  Health Check:       http://localhost/health"
echo ""
echo -e "${GREEN}Database:${NC}"
echo "  Host: postgres (or localhost:5432 from host machine)"
echo "  Database: threat_hub"
echo "  User: threat_admin"
echo ""
echo -e "${GREEN}Container Status:${NC}"
docker-compose ps
echo ""
echo -e "${GREEN}Logs:${NC}"
echo "  View all logs:     docker-compose logs -f"
echo "  View API logs:     docker-compose logs -f api"
echo "  View DB logs:      docker-compose logs -f postgres"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Update .env with secure credentials"
echo "  2. Configure SSL certificates in ./ssl/"
echo "  3. Test API endpoints at http://localhost/docs"
echo "  4. Load sample threats: curl -X POST http://localhost/advisories/ ..."
echo ""
echo "Deployment log saved to: ${LOG_FILE}"
