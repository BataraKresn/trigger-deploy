#!/bin/bash
set -e
trap 'echo "❌ Update failed at line $LINENO"; exit 1;' ERR

start_time=$(date +%s)
start_fmt=$(date "+%Y-%m-%d %H:%M:%S")

echo "📁 [$start_fmt] Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found, copying from .env.example"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from template"
        echo "🔔 Please review and update .env file with your configurations"
    else
        echo "❌ .env.example not found! Please create .env file manually"
        exit 1
    fi
else
    echo "✅ .env file found"
fi

echo "🔑 Checking SSH configuration..."
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "⚠️  SSH private key not found at ~/.ssh/id_rsa"
    echo "   This might cause issues with deployment functionality"
fi

if [ ! -f ~/.ssh/known_hosts ]; then
    echo "⚠️  SSH known_hosts not found, creating empty file"
    mkdir -p ~/.ssh
    touch ~/.ssh/known_hosts
    echo "✅ Created SSH known_hosts file"
fi

echo "📁 Ensuring required directories exist..."
for dir in ./data/postgres ./logs ./trigger-logs ./config; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "📂 Created: $dir"
    else
        echo "📂 Exists: $dir"
    fi
done

# Set proper permissions
chmod -R 755 ./data/ ./logs/ ./trigger-logs/ 2>/dev/null || true

echo "✅ Directory check complete"

echo "🔧 Ensuring network 'dev-trigger-network' exists with correct configuration..."
if ! docker network ls | grep -q 'dev-trigger-network'; then
    echo "🌐 Creating Docker network: dev-trigger-network"
    docker network create --driver bridge --subnet 172.20.0.0/16 --gateway 172.20.0.1 dev-trigger-network
else
    echo "✅ Network 'dev-trigger-network' already exists"
    # Check if network has compose labels, if yes remove it to avoid conflicts
    if docker network inspect dev-trigger-network --format '{{.Labels}}' | grep -q 'com.docker.compose'; then
        echo "🔄 Removing compose labels from existing network..."
        docker network rm dev-trigger-network 2>/dev/null || true
        echo "🌐 Recreating Docker network: dev-trigger-network"
        docker network create --driver bridge --subnet 172.20.0.0/16 --gateway 172.20.0.1 dev-trigger-network
    fi
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
