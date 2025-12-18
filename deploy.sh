#!/bin/bash
#
# Deployment script for WP_Pro-FM Admin Interface
# Usage: ./deploy.sh
#

set -e

echo "=========================================="
echo "  WP_Pro-FM Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from the WP_Pro-FM directory."
    exit 1
fi

print_status "Starting deployment..."

# Step 1: Pull latest changes (if git repo)
if [ -d ".git" ]; then
    print_status "Pulling latest changes from git..."
    git pull origin main || print_warning "Git pull failed or not configured"
fi

# Step 2: Stop existing containers
print_status "Stopping existing containers..."
docker compose down --remove-orphans || true

# Step 3: Build new images
print_status "Building Docker images..."
docker compose build --no-cache backend

# Step 4: Start containers
print_status "Starting containers..."
docker compose up -d

# Step 5: Wait for containers to be ready
print_status "Waiting for containers to be ready..."
sleep 10

# Step 6: Run migrations
print_status "Running database migrations..."
docker compose exec -T backend python manage.py migrate --noinput

# Step 7: Collect static files
print_status "Collecting static files..."
docker compose exec -T backend python manage.py collectstatic --noinput

# Step 8: Verify deployment
print_status "Verifying deployment..."
if docker compose ps | grep -q "backend.*Up"; then
    print_status "Backend container is running"
else
    print_error "Backend container is not running!"
    docker compose logs backend
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  Deployment completed successfully!${NC}"
echo "=========================================="
echo ""
echo "Admin interface available at:"
echo "  - Local: http://localhost:8001/admin/"
echo "  - Production: https://admin.profm24.de/admin/"
echo ""
