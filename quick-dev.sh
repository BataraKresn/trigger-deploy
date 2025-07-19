#!/bin/bash

# Deploy Server - Development Quick Commands
# Save this file as: quick-dev.sh

echo "🚀 Deploy Server Development Commands"
echo "====================================="

show_help() {
    echo "Usage: ./quick-dev.sh [command]"
    echo ""
    echo "Available commands:"
    echo "  start       - Start all services (development mode)"
    echo "  start-prod  - Start all services (production mode)"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  logs        - Show logs for all services"
    echo "  backend     - Show backend logs only"
    echo "  frontend    - Show frontend logs only"
    echo "  db          - Connect to database"
    echo "  migrate     - Run database migrations"
    echo "  reset       - Reset database (⚠️ destructive)"
    echo "  status      - Show services status"
    echo "  build       - Rebuild all images"
    echo "  clean       - Clean up Docker resources"
    echo ""
}

case "$1" in
    "start")
        echo "🟢 Starting all services in development mode..."
        docker-compose up -d
        echo "✅ Services started. Access:"
        echo "   Frontend: http://localhost:3111"
        echo "   Backend:  http://localhost:5002/api"
        echo "   Docs:     http://localhost:5002/docs"
        echo "   Environment: Development"
        ;;
    "start-prod")
        echo "🟢 Starting all services in production mode..."
        docker-compose -f docker-compose.prod.yml up -d
        echo "✅ Services started. Access:"
        echo "   Frontend: http://localhost:3111"
        echo "   Backend:  http://localhost:5002/api"
        echo "   Docs:     http://localhost:5002/docs"
        echo "   Environment: Production"
        ;;
    "stop")
        echo "🔴 Stopping all services..."
        docker-compose down
        ;;
    "restart")
        echo "🔄 Restarting all services..."
        docker-compose restart
        ;;
    "logs")
        echo "📋 Showing logs for all services..."
        docker-compose logs -f
        ;;
    "backend")
        echo "📋 Showing backend logs..."
        docker-compose logs -f backend
        ;;
    "frontend")
        echo "📋 Showing frontend logs..."
        docker-compose logs -f frontend
        ;;
    "db")
        echo "🗄️ Connecting to database..."
        docker-compose exec postgres psql -U deployuser -d deploydb
        ;;
    "migrate")
        echo "🔄 Running database migrations..."
        docker-compose exec backend ./init-migrations.sh
        ;;
    "reset")
        echo "⚠️ Resetting database (this will delete all data)..."
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            docker-compose up -d postgres
            sleep 10
            docker-compose exec backend ./init-migrations.sh
            echo "✅ Database reset complete"
        else
            echo "❌ Database reset cancelled"
        fi
        ;;
    "status")
        echo "📊 Services status:"
        docker-compose ps
        echo ""
        echo "📈 Resource usage:"
        docker stats --no-stream
        ;;
    "build")
        echo "🔨 Rebuilding all images..."
        docker-compose build --no-cache
        ;;
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker system prune -af
        echo "✅ Cleanup complete"
        ;;
    *)
        show_help
        ;;
esac
