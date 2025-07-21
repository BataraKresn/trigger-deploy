#!/bin/bash
# Simple setup script untuk first-time deployment

set -e

echo "🚀 Trigger Deploy - First Time Setup"
echo "=================================="

# Buat direktori yang diperlukan
echo "📁 Creating required directories..."
mkdir -p ./data/postgres
mkdir -p ./logs
mkdir -p ./trigger-logs
mkdir -p ./config
chmod 755 ./data/postgres
echo "✅ Directories created"

# Copy environment file jika belum ada
if [ ! -f ".env" ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Buat config files jika belum ada
if [ ! -f "./config/servers.json" ]; then
    echo "⚙️ Creating default servers.json..."
    cat > ./config/servers.json << 'EOF'
[
  {
    "name": "Example Server",
    "ip": "192.168.1.100",
    "user": "ubuntu",
    "description": "Example production server",
    "alias": "example-server",
    "path": "/home/ubuntu/app",
    "type": "Production Server",
    "port": 22
  }
]
EOF
    echo "✅ Default servers.json created"
fi

if [ ! -f "./config/services.json" ]; then
    echo "⚙️ Creating default services.json..."
    cat > ./config/services.json << 'EOF'
[
  {
    "name": "Example Website",
    "url": "https://example.com",
    "check_interval": 300,
    "timeout": 10
  }
]
EOF
    echo "✅ Default services.json created"
fi

# Cleanup existing Docker resources
echo "🧹 Cleaning up existing Docker resources..."
docker compose down --remove-orphans 2>/dev/null || true
docker volume rm dev-trigger_postgres_data 2>/dev/null || true
docker network rm dev-trigger-network 2>/dev/null || true

# Buat network
echo "🌐 Creating Docker network..."
docker network create --driver bridge --subnet 172.20.0.0/16 --gateway 172.20.0.1 dev-trigger-network

# Build dan start services
echo "🔨 Building and starting services..."
docker compose build --no-cache
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check status
echo "🔍 Checking service status..."
docker compose ps

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🌐 Your Trigger Deploy Server is now running at:"
echo "   - Landing Page: http://localhost:3111"
echo "   - Dashboard: http://localhost:3111/home"
echo "   - Login: http://localhost:3111/login"
echo ""
echo "🔐 Default credentials:"
echo "   - Password: admin123"
echo "   - Deploy Token: SATindonesia2026"
echo ""
echo "📊 Useful commands:"
echo "   - View logs: docker compose logs -f"
echo "   - Stop services: docker compose down"
echo "   - Restart: docker compose restart"
echo ""
