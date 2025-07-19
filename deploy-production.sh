#!/bin/bash

# Deploy Server - Production Deployment Script
# Save this file as: deploy-production.sh

set -e  # Exit on any error

echo "🚀 Deploy Server - Production Deployment"
echo "========================================"

# Configuration
APP_DIR="/opt/deploy-server"
REPO_URL="https://github.com/BataraKresn/trigger-deploy.git"
BRANCH="main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if user can run Docker commands
    if ! docker ps &> /dev/null; then
        log_error "Cannot run Docker commands. Please add user to docker group or run as root."
        exit 1
    fi
    
    log_info "✅ All requirements met"
}

setup_directories() {
    log_info "Setting up directories..."
    
    # Create app directory if it doesn't exist
    if [ ! -d "$APP_DIR" ]; then
        sudo mkdir -p "$APP_DIR"
        sudo chown $USER:$USER "$APP_DIR"
        log_info "Created directory: $APP_DIR"
    fi
    
    cd "$APP_DIR"
}

deploy_application() {
    log_info "Deploying application..."
    
    # Clone or update repository
    if [ ! -d ".git" ]; then
        log_info "Cloning repository..."
        git clone "$REPO_URL" .
    else
        log_info "Updating repository..."
        git fetch origin
        git reset --hard origin/$BRANCH
    fi
    
    # Setup environment files
    if [ ! -f "backend/.env.production" ]; then
        log_error "backend/.env.production not found!"
        exit 1
    fi
    
    if [ ! -f "frontend/.env.production" ]; then
        log_error "frontend/.env.production not found!"
        exit 1
    fi
    
    log_info "Using production environment files"
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker-compose -f docker-compose.prod.yml down || true
    
    # Build and start services
    log_info "Building and starting services in production mode..."
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30
    
    # Initialize database
    log_info "Initializing database..."
    docker-compose exec -T backend ./init-migrations.sh
    
    log_info "✅ Deployment completed successfully!"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if services are running
    if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_error "Some services are not running properly"
        docker-compose -f docker-compose.prod.yml ps
        exit 1
    fi
    
    # Test health endpoints
    log_info "Testing health endpoints..."
    
    # Test backend health
    if curl -f http://localhost:5002/health &> /dev/null; then
        log_info "✅ Backend health check passed"
    else
        log_error "❌ Backend health check failed"
    fi
    
    # Test frontend
    if curl -f http://localhost:3111 &> /dev/null; then
        log_info "✅ Frontend health check passed"
    else
        log_error "❌ Frontend health check failed"
    fi
    
    log_info "Deployment verification completed"
}

show_access_info() {
    echo ""
    echo "🎉 Deployment Successful!"
    echo "========================"
    echo ""
    echo "Access your application at:"
    echo "  Frontend: http://$(hostname -I | awk '{print $1}'):3111"
    echo "  Backend:  http://$(hostname -I | awk '{print $1}'):5002/api"
    echo "  API Docs: http://$(hostname -I | awk '{print $1}'):5002/docs"
    echo ""
    echo "Management commands:"
    echo "  View logs:     docker-compose -f docker-compose.prod.yml logs -f"
    echo "  Stop services: docker-compose -f docker-compose.prod.yml down"
    echo "  Start services: docker-compose -f docker-compose.prod.yml up -d"
    echo "  Update app:    ./deploy-production.sh update"
    echo ""
}

update_application() {
    log_info "Updating application..."
    
    cd "$APP_DIR"
    
    # Pull latest changes
    git pull origin $BRANCH
    
    # Rebuild and restart services
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d --build
    
    # Run any new migrations
    docker-compose -f docker-compose.prod.yml exec -T backend flask db upgrade
    
    log_info "✅ Application updated successfully!"
}

# Main execution
case "${1:-deploy}" in
    "deploy")
        check_requirements
        setup_directories
        deploy_application
        verify_deployment
        show_access_info
        ;;
    "update")
        update_application
        ;;
    "check")
        check_requirements
        ;;
    *)
        echo "Usage: $0 [deploy|update|check]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  update  - Update existing deployment"
        echo "  check   - Check system requirements"
        exit 1
        ;;
esac
