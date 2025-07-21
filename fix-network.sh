#!/bin/bash
# Script untuk membersihkan dan membuat ulang network Docker

set -e

echo "🧹 Cleaning up Docker network issues..."

# Stop semua container yang menggunakan network
echo "🛑 Stopping containers..."
docker compose down 2>/dev/null || true

# Hapus network yang bermasalah
echo "🗑️ Removing problematic network..."
docker network rm dev-trigger-network 2>/dev/null || true

# Buat ulang network dengan konfigurasi yang benar
echo "🌐 Creating new network with correct configuration..."
docker network create --driver bridge --subnet 172.20.0.0/16 --gateway 172.20.0.1 dev-trigger-network

# Jalankan ulang aplikasi
echo "🚀 Starting application..."
docker compose up -d

echo "✅ Network cleanup completed!"
echo "🔍 You can verify with: docker network inspect dev-trigger-network"
