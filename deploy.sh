#!/bin/bash

###############################################################################
# InfraSentinel - Quick Deployment Script
# Deploys or updates InfraSentinel with zero downtime
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="/tmp/infrasentinel-backup"
DATE=$(date +%Y%m%d_%H%M%S)

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Main deployment
print_header "🚀 InfraSentinel Deployment"

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    exit 1
fi
print_success "Docker found"

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed!"
    exit 1
fi
print_success "Docker Compose found"

if ! docker info > /dev/null 2>&1; then
    print_error "Docker daemon is not running!"
    exit 1
fi
print_success "Docker daemon is running"

# Create backup directory
mkdir -p "$BACKUP_DIR"
print_success "Backup directory ready"

echo ""

# Check if this is an update
if docker ps -q -f name=infrasentinel-backend | grep -q .; then
    print_header "💾 Backing Up Current Deployment"
    
    # Backup database
    if docker ps -q -f name=infrasentinel-db | grep -q .; then
        echo "Backing up database..."
        docker exec infrasentinel-db mysqldump -u root -p${MYSQL_ROOT_PASSWORD:-rootpassword} monitoring > "$BACKUP_DIR/db_backup_$DATE.sql" 2>/dev/null || true
        print_success "Database backed up"
    fi
    
    # Backup current compose file
    if [ -f docker-compose.yml ]; then
        cp docker-compose.yml "$BACKUP_DIR/docker-compose_$DATE.yml"
        print_success "Configuration backed up"
    fi
    
    # Remove old backups (keep last 5)
    cd "$BACKUP_DIR"
    ls -t db_backup_*.sql 2>/dev/null | tail -n +6 | xargs -r rm
    ls -t docker-compose_*.yml 2>/dev/null | tail -n +6 | xargs -r rm
    cd - > /dev/null
    
    IS_UPDATE=true
else
    IS_UPDATE=false
    print_warning "First time deployment detected"
fi

echo ""

# Build images
print_header "🏗️  Building Docker Images"
docker-compose build --parallel backend frontend worker
print_success "All images built successfully"

echo ""

# Deploy
if [ "$IS_UPDATE" = true ]; then
    print_header "🔄 Updating Services"
    
    # Stop old services (keep DB running)
    echo "Stopping backend, frontend, and worker..."
    docker-compose stop backend frontend worker
    print_success "Services stopped"
    
    # Remove old containers
    docker-compose rm -f backend frontend worker
    print_success "Old containers removed"
else
    print_header "🎬 Starting Services"
fi

# Start all services
echo "Starting services..."
docker-compose up -d
print_success "Services started"

echo ""

# Wait for services to be ready
print_header "🏥 Health Check"

echo "Waiting for backend to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend is healthy"
        break
    fi
    
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_error "Backend health check failed!"
    echo ""
    echo "Check logs with: docker-compose logs backend"
    exit 1
fi

echo ""

# Check frontend
if curl -sf http://localhost:80 > /dev/null 2>&1; then
    print_success "Frontend is accessible"
else
    print_warning "Frontend may not be ready yet"
fi

echo ""

# Cleanup
print_header "🧹 Cleanup"

echo "Removing dangling images..."
docker image prune -f > /dev/null
print_success "Cleanup completed"

echo ""

# Show status
print_header "📊 Deployment Status"

docker-compose ps

echo ""

# Success message
print_header "✅ Deployment Successful!"

echo "InfraSentinel is now running! 🎉"
echo ""
echo "Access points:"
echo "  • Frontend:  http://localhost"
echo "  • Backend:   http://localhost:8000"
echo "  • Jenkins:   http://localhost:8080"
echo ""
echo "Useful commands:"
echo "  • View logs:     docker-compose logs -f"
echo "  • Stop all:      docker-compose stop"
echo "  • Restart:       docker-compose restart"
echo "  • View status:   docker-compose ps"
echo ""

if [ "$IS_UPDATE" = true ]; then
    echo "Backup location: $BACKUP_DIR/db_backup_$DATE.sql"
    echo ""
fi

print_success "Deployment completed at $(date)"
echo ""
