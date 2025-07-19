#!/bin/bash

# Deploy Server Stack Manager
# This script manages the entire Deploy Server stack

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Deploy Server Stack Manager"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the entire stack (database, backend, frontend)"
    echo "  stop      Stop the entire stack"
    echo "  restart   Restart the entire stack"
    echo "  build     Build all containers"
    echo "  logs      Show logs for all services"
    echo "  status    Show status of all services"
    echo "  clean     Clean up containers and volumes"
    echo "  init      Initialize database and create sample data"
    echo "  shell     Open shell in backend container"
    echo "  help      Show this help message"
    echo ""
    echo "Service-specific commands:"
    echo "  logs-backend   Show backend logs"
    echo "  logs-frontend  Show frontend logs"
    echo "  logs-db        Show database logs"
    echo ""
    echo "Development commands:"
    echo "  dev-backend    Start backend in development mode"
    echo "  dev-frontend   Start frontend in development mode"
}

# Function to check if Docker and Docker Compose are available
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
        print_warning ".env file not found in backend directory"
        print_status "Creating default .env file..."
        
        cat > "$PROJECT_ROOT/backend/.env" << EOF
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-key-change-in-production

# Database Configuration
DATABASE_URL=postgresql://deployuser:deploypass@postgres:5432/deploydb
POSTGRES_USER=deployuser
POSTGRES_PASSWORD=deploypass
POSTGRES_DB=deploydb

# Application Configuration
API_HOST=0.0.0.0
API_PORT=5001
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
MAX_CONTENT_LENGTH=16777216

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=logs/backend.log

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
RATELIMIT_DEFAULT=100 per hour

# Security
PASSWORD_MIN_LENGTH=6
SESSION_TIMEOUT=3600
EOF
        print_success "Default .env file created"
    fi
}

# Function to start the stack
start_stack() {
    print_status "Starting Deploy Server stack..."
    check_env_file
    
    cd "$PROJECT_ROOT"
    docker-compose up -d
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check if backend is ready
    for i in {1..30}; do
        if curl -s http://localhost:5001/api/health > /dev/null 2>&1; then
            print_success "Backend is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Backend health check timeout, but continuing..."
        fi
        sleep 2
    done
    
    print_success "Deploy Server stack started successfully!"
    print_status "Services running:"
    print_status "  - Frontend: http://localhost:3000"
    print_status "  - Backend API: http://localhost:5001/api"
    print_status "  - API Documentation: http://localhost:5001/docs"
    print_status "  - Database: localhost:5432"
    print_status ""
    print_status "Default credentials:"
    print_status "  - Admin: admin/admin123"
    print_status "  - Demo: demo/demo123"
}

# Function to stop the stack
stop_stack() {
    print_status "Stopping Deploy Server stack..."
    cd "$PROJECT_ROOT"
    docker-compose down
    print_success "Deploy Server stack stopped"
}

# Function to restart the stack
restart_stack() {
    print_status "Restarting Deploy Server stack..."
    stop_stack
    sleep 2
    start_stack
}

# Function to build containers
build_containers() {
    print_status "Building containers..."
    cd "$PROJECT_ROOT"
    docker-compose build --no-cache
    print_success "Containers built successfully"
}

# Function to show logs
show_logs() {
    cd "$PROJECT_ROOT"
    docker-compose logs -f
}

# Function to show status
show_status() {
    print_status "Deploy Server stack status:"
    cd "$PROJECT_ROOT"
    docker-compose ps
}

# Function to clean up
clean_stack() {
    print_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up..."
        cd "$PROJECT_ROOT"
        docker-compose down -v --rmi all --remove-orphans
        docker system prune -f
        print_success "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to initialize database
init_database() {
    print_status "Initializing database..."
    cd "$PROJECT_ROOT"
    
    # Ensure backend is running
    if ! docker-compose ps backend | grep -q "Up"; then
        print_status "Starting backend service..."
        docker-compose up -d backend postgres
        sleep 10
    fi
    
    # Run initialization script
    docker-compose exec backend bash -c "cd /app && ./init-deploy-server.sh"
    print_success "Database initialization completed"
}

# Function to open shell in backend
backend_shell() {
    print_status "Opening shell in backend container..."
    cd "$PROJECT_ROOT"
    docker-compose exec backend bash
}

# Function to show service-specific logs
show_backend_logs() {
    cd "$PROJECT_ROOT"
    docker-compose logs -f backend
}

show_frontend_logs() {
    cd "$PROJECT_ROOT"
    docker-compose logs -f frontend
}

show_db_logs() {
    cd "$PROJECT_ROOT"
    docker-compose logs -f postgres
}

# Function to start backend in development mode
dev_backend() {
    print_status "Starting backend in development mode..."
    cd "$PROJECT_ROOT/backend"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Start development server
    export FLASK_ENV=development
    export FLASK_DEBUG=True
    python app.py
}

# Function to start frontend in development mode
dev_frontend() {
    print_status "Starting frontend in development mode..."
    cd "$PROJECT_ROOT/frontend"
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        print_status "Installing dependencies..."
        npm install
    fi
    
    # Start development server
    npm run dev
}

# Main script logic
case "${1:-help}" in
    start)
        check_dependencies
        start_stack
        ;;
    stop)
        check_dependencies
        stop_stack
        ;;
    restart)
        check_dependencies
        restart_stack
        ;;
    build)
        check_dependencies
        build_containers
        ;;
    logs)
        check_dependencies
        show_logs
        ;;
    status)
        check_dependencies
        show_status
        ;;
    clean)
        check_dependencies
        clean_stack
        ;;
    init)
        check_dependencies
        init_database
        ;;
    shell)
        check_dependencies
        backend_shell
        ;;
    logs-backend)
        check_dependencies
        show_backend_logs
        ;;
    logs-frontend)
        check_dependencies
        show_frontend_logs
        ;;
    logs-db)
        check_dependencies
        show_db_logs
        ;;
    dev-backend)
        dev_backend
        ;;
    dev-frontend)
        dev_frontend
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
