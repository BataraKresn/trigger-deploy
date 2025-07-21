#!/bin/bash

# =================================
# Fix PostgreSQL Authentication & Dependencies
# =================================

echo "🔧 Fixing PostgreSQL Authentication and Dependencies..."

# Stop current containers
echo "⏹️ Stopping containers..."
docker-compose down

# Remove existing images to force rebuild
echo "🗑️ Removing old images..."
docker rmi dev-trigger-deploy:latest 2>/dev/null || true

# Build with no cache to ensure all new dependencies are installed
echo "🔨 Building new container with updated dependencies..."
docker-compose build --no-cache dev-trigger-deploy

# Start the services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "📊 Checking service status..."
docker-compose ps

# Show application logs
echo "📋 Application logs:"
docker-compose logs --tail=20 dev-trigger-deploy

echo ""
echo "✅ Fix completed!"
echo ""
echo "🌐 Access your application at:"
echo "   • Dashboard: http://localhost:3111/home"
echo "   • Login: http://localhost:3111/login"
echo "   • API Health: http://localhost:3111/api/health"
echo ""
echo "🔑 Default credentials:"
echo "   • Username: admin"
echo "   • Password: admin123"
echo ""
echo "📊 To check logs: docker-compose logs -f dev-trigger-deploy"
echo "🛠️ To check database: docker-compose exec postgres psql -U trigger_deploy_user -d trigger_deploy"
