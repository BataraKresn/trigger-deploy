#!/bin/bash
set -e
trap 'echo "❌ Update failed at line $LINENO"; exit 1;' ERR

start_time=$(date +%s)
start_fmt=$(date "+%Y-%m-%d %H:%M:%S")

echo "🔄 [$start_fmt] Rebuilding Docker image with no cache..."
# docker compose build --no-cache > /dev/null 2>&1
docker compose build
echo "✅ Docker image rebuilt successfully!"

echo "🚀 Restarting container..."
# docker compose up -d > /dev/null 2>&1
docker compose up -d

end_time=$(date +%s)
end_fmt=$(date "+%Y-%m-%d %H:%M:%S")
runtime=$((end_time - start_time))
minutes=$((runtime / 60))
seconds=$((runtime % 60))

echo "✅ [$end_fmt] Docker service updated and running!"
echo "⏱️ Total update time: ${minutes}m ${seconds}s"