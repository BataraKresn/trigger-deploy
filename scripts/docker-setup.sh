#!/bin/bash

# Docker Compose Setup Script
# Ensures all required directories and files exist before running docker-compose

echo "🚀 Setting up Docker environment..."

# Create required directories
mkdir -p data/postgres
mkdir -p logs
mkdir -p trigger-logs
mkdir -p config

echo "✅ Created required directories"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found, copying from .env.example"
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "🔔 Please review and update .env file with your configurations"
else
    echo "✅ .env file exists"
fi

# Check SSH keys
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "⚠️  SSH private key not found at ~/.ssh/id_rsa"
    echo "   This might cause issues with deployment functionality"
fi

if [ ! -f ~/.ssh/known_hosts ]; then
    echo "⚠️  SSH known_hosts not found at ~/.ssh/known_hosts"
    echo "   Creating empty known_hosts file"
    mkdir -p ~/.ssh
    touch ~/.ssh/known_hosts
fi

# Set proper permissions
chmod -R 755 data/
chmod -R 755 logs/
chmod -R 755 trigger-logs/

echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Review .env file: nano .env"
echo "2. Start services: docker-compose up -d"
echo "3. Check logs: docker-compose logs -f"
