#!/bin/bash
# =================================
# Database Switching Helper Script
# =================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"
DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

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

# Function to backup .env file
backup_env() {
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        print_success "Created backup of .env file"
    fi
}

# Function to update .env for local database
setup_local_database() {
    print_status "Configuring for local PostgreSQL database..."
    
    backup_env
    
    # Update .env file
    sed -i 's/^POSTGRES_DB=.*/POSTGRES_DB=trigger_deploy/' "$ENV_FILE"
    sed -i 's/^POSTGRES_USER=.*/POSTGRES_USER=trigger_deploy_user/' "$ENV_FILE"
    sed -i 's/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=secure_password_123/' "$ENV_FILE"
    sed -i 's/^POSTGRES_HOST=.*/POSTGRES_HOST=postgres/' "$ENV_FILE"
    sed -i 's/^POSTGRES_PORT=.*/POSTGRES_PORT=5432/' "$ENV_FILE"
    sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://trigger_deploy_user:secure_password_123@postgres:5432/trigger_deploy|' "$ENV_FILE"
    
    # Update docker-compose.yml to enable local postgres
    sed -i 's/^    # profiles:/    profiles:/' "$DOCKER_COMPOSE_FILE"
    sed -i 's/^    #   - local-only/      - local-only/' "$DOCKER_COMPOSE_FILE"
    
    print_success "Configured for local PostgreSQL database"
    print_status "Run: docker-compose up -d"
}

# Function to update .env for external database
setup_external_database() {
    local host="$1"
    local port="$2"
    local database="$3"
    local user="$4"
    local password="$5"
    
    if [ -z "$host" ] || [ -z "$port" ] || [ -z "$database" ] || [ -z "$user" ] || [ -z "$password" ]; then
        print_error "Missing required parameters for external database"
        echo "Usage: $0 external <host> <port> <database> <user> <password>"
        exit 1
    fi
    
    print_status "Configuring for external PostgreSQL database..."
    print_status "Host: $host:$port"
    print_status "Database: $database"
    print_status "User: $user"
    
    backup_env
    
    # Update .env file
    sed -i "s/^POSTGRES_DB=.*/POSTGRES_DB=$database/" "$ENV_FILE"
    sed -i "s/^POSTGRES_USER=.*/POSTGRES_USER=$user/" "$ENV_FILE"
    sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$password/" "$ENV_FILE"
    sed -i "s/^POSTGRES_HOST=.*/POSTGRES_HOST=$host/" "$ENV_FILE"
    sed -i "s/^POSTGRES_PORT=.*/POSTGRES_PORT=$port/" "$ENV_FILE"
    sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://$user:$password@$host:$port/$database|" "$ENV_FILE"
    
    # Update docker-compose.yml to disable local postgres and use host networking
    sed -i 's/^    profiles:/    # profiles:/' "$DOCKER_COMPOSE_FILE"
    sed -i 's/^      - local-only/    #   - local-only/' "$DOCKER_COMPOSE_FILE"
    sed -i 's/^    # network_mode: host/    network_mode: host/' "$DOCKER_COMPOSE_FILE"
    sed -i 's/^    networks:/    # networks:/' "$DOCKER_COMPOSE_FILE"
    sed -i 's/^      - dev-trigger-network/    #   - dev-trigger-network/' "$DOCKER_COMPOSE_FILE"
    sed -i 's/^    depends_on:/    # depends_on:/' "$DOCKER_COMPOSE_FILE"
    sed -i 's/^      postgres:/    #   postgres:/' "$DOCKER_COMPOSE_FILE"
    sed -i 's/^        condition: service_healthy/    #     condition: service_healthy/' "$DOCKER_COMPOSE_FILE"
    
    print_success "Configured for external PostgreSQL database"
    print_status "Testing connectivity..."
    
    # Test connectivity
    if command -v python3 >/dev/null 2>&1; then
        python3 "$SCRIPT_DIR/test-db-connectivity.py"
    else
        print_warning "Python3 not found, skipping connectivity test"
    fi
    
    print_status "Run: docker-compose up -d"
}

# Function to test current database connection
test_connection() {
    print_status "Testing current database connection..."
    
    if command -v python3 >/dev/null 2>&1; then
        python3 "$SCRIPT_DIR/test-db-connectivity.py"
    else
        print_error "Python3 not found, cannot run connectivity test"
        exit 1
    fi
}

# Function to show current configuration
show_config() {
    print_status "Current database configuration:"
    echo
    if [ -f "$ENV_FILE" ]; then
        grep -E "^(POSTGRES_|DATABASE_URL)" "$ENV_FILE" | while IFS= read -r line; do
            echo "  $line"
        done
    else
        print_error ".env file not found"
    fi
}

# Function to show help
show_help() {
    echo "Database Configuration Helper"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  local                           - Configure for local PostgreSQL (Docker)"
    echo "  external <host> <port> <db> <user> <pass> - Configure for external PostgreSQL"
    echo "  test                            - Test current database connection"
    echo "  config                          - Show current configuration"
    echo "  help                            - Show this help"
    echo
    echo "Examples:"
    echo "  $0 local"
    echo "  $0 external 30.30.30.11 5456 mydb myuser mypass"
    echo "  $0 test"
    echo "  $0 config"
    echo
}

# Main script logic
case "${1:-}" in
    local)
        setup_local_database
        ;;
    external)
        setup_external_database "$2" "$3" "$4" "$5" "$6"
        ;;
    test)
        test_connection
        ;;
    config)
        show_config
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: ${1:-}"
        echo
        show_help
        exit 1
        ;;
esac
