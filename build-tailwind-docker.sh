#!/bin/bash
# Alternative build script untuk environment tanpa Node.js
# Menggunakan Docker untuk build Tailwind CSS

echo "🎨 Building Tailwind CSS with Docker..."

# Check if Docker available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker tidak ditemukan. Install Docker atau gunakan build-tailwind.sh dengan Node.js"
    exit 1
fi

# Create temporary Dockerfile for CSS build only
cat > Dockerfile.tailwind << 'EOF'
FROM node:18-alpine AS builder
WORKDIR /build
RUN npm install -g tailwindcss
COPY templates/ ./templates/
COPY static/ ./static/
COPY tailwind.config.js ./
COPY static/css/input.css ./
RUN tailwindcss -i input.css -o output.css --minify

FROM scratch
COPY --from=builder /build/output.css /
EOF

# Build CSS using Docker
echo "🔨 Building CSS with Docker..."
docker build -f Dockerfile.tailwind -t tailwind-builder .

# Extract CSS from container
echo "📦 Extracting built CSS..."
docker run --rm tailwind-builder cat /output.css > static/css/tailwind.css

# Cleanup
rm Dockerfile.tailwind

if [ $? -eq 0 ]; then
    echo "✅ Tailwind CSS berhasil di-build dengan Docker!"
    echo "📄 Output: static/css/tailwind.css"
    echo "📊 File size: $(du -h static/css/tailwind.css | cut -f1)"
else
    echo "❌ Build gagal!"
    exit 1
fi
