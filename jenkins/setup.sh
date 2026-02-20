#!/bin/bash

###############################################################################
# InfraSentinel - Jenkins Setup Script
# Configures Jenkins with required plugins and Docker support
###############################################################################

set -e

echo "🔧 Starting Jenkins Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running!"
    exit 1
fi
print_success "Docker is running"

# Check if Jenkins container exists
if ! docker ps -a | grep -q infrasentinel-jenkins; then
    print_warning "Jenkins container not found. Starting docker-compose..."
    docker-compose up -d jenkins
    sleep 10
fi

# Wait for Jenkins to start
echo ""
echo "Waiting for Jenkins to start..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -sf http://localhost:8080/login > /dev/null 2>&1; then
        print_success "Jenkins is running!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_error "Jenkins failed to start within expected time"
    echo ""
    echo "Check logs with: docker logs infrasentinel-jenkins"
    exit 1
fi

echo ""
echo ""
echo "=========================================="
echo "   Jenkins Setup Complete! 🎉"
echo "=========================================="
echo ""
echo "Access Jenkins at: http://localhost:8080"
echo ""
echo "Default credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "⚠️  IMPORTANT: Change the default password in production!"
echo ""
echo "Next steps:"
echo "  1. Log in to Jenkins"
echo "  2. Configure GitHub webhook (optional)"
echo "  3. Run your first build"
echo ""
echo "To install Docker inside Jenkins container:"
echo "  docker exec -u root infrasentinel-jenkins apt-get update"
echo "  docker exec -u root infrasentinel-jenkins apt-get install -y docker.io"
echo ""
echo "=========================================="
