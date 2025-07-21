#!/bin/bash
set -e
trap 'echo "❌ Update failed at line $LINENO"; exit 1;' ERR

start_time=$(date +%s)
start_fmt=$(date "+%Y-%m-%d %H:%M:%S")

echo "📁 [$start_fmt] Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found, using defaults"
else
    echo "✅ .env file found"
fi

echo "📁 Creating required directories..."
mkdir -p ./data/postgres
mkdir -p ./logs
mkdir -p ./trigger-logs
mkdir -p ./config
echo "✅ Directories created"

echo "🔧 Ensuring network 'dev-trigger-network' exists with correct configuration..."
if ! docker network ls | grep -q 'dev-trigger-network'; then
    echo "🌐 Creating Docker network: dev-trigger-network"
    docker network create --driver bridge --subnet 172.20.0.0/16 --gateway 172.20.0.1 dev-trigger-network
else
    echo "✅ Network 'dev-trigger-network' already exists"
fi

echo "🔄 [$start_fmt] Rebuilding Docker image with no cache..."
docker compose build --no-cache

echo "🚀 Restarting container..."
docker compose up -d

end_time=$(date +%s)
end_fmt=$(date "+%Y-%m-%d %H:%M:%S")
runtime=$((end_time - start_time))
minutes=$((runtime / 60))
seconds=$((runtime % 60))

echo "✅ [$end_fmt] Docker service updated and running!"
echo "⏱️ Total update time: ${minutes}m ${seconds}s"
