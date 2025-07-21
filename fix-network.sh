#!/bin/bash
# Script untuk membersihkan dan memperbaiki masalah Docker

set -e

echo "🧹 Cleaning up Docker issues..."

# Stop semua container yang menggunakan network
echo "🛑 Stopping containers..."
docker compose down 2>/dev/null || true

# Hapus volume yang bermasalah (optional)
echo "🗑️ Removing old volumes (if any)..."
docker volume rm dev-trigger_postgres_data 2>/dev/null || true

# Hapus network yang bermasalah
echo "🗑️ Removing problematic network..."
docker network rm dev-trigger-network 2>/dev/null || true

# Buat direktori yang diperlukan
echo "📁 Creating required directories..."
mkdir -p ./data/postgres
mkdir -p ./logs
mkdir -p ./trigger-logs
mkdir -p ./config
echo "✅ Directories created"

# Buat ulang network dengan konfigurasi yang benar
echo "🌐 Creating new network with correct configuration..."
docker network create --driver bridge --subnet 172.20.0.0/16 --gateway 172.20.0.1 dev-trigger-network

# Jalankan ulang aplikasi
echo "🚀 Starting application..."
docker compose up -d

echo "✅ Cleanup and setup completed!"
echo "🔍 You can verify with:"
echo "  - docker network inspect dev-trigger-network"
echo "  - docker compose ps"
echo "  - docker volume ls"
