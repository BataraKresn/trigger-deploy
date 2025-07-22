#!/bin/bash
# Build Tailwind CSS via Docker using standalone binary (tidak perlu Node.js lokal)

echo "🎨 Building Tailwind CSS with Docker..."

# Cek Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker tidak ditemukan. Harap install Docker terlebih dahulu."
    exit 1
fi

# Buat Dockerfile sementara
cat > Dockerfile.tailwind << 'EOF'
FROM alpine:3.19

WORKDIR /build

RUN apk add --no-cache curl

# Ambil Tailwind CSS binary
RUN curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.0/tailwindcss-linux-x64 \
    && mv tailwindcss-linux-x64 tailwindcss \
    && chmod +x tailwindcss

# Salin konfigurasi & input
COPY tailwind.config.js ./
COPY static/css/input.css ./
COPY templates/ ./templates/
COPY static/ ./static/

# Build CSS
RUN ./tailwindcss -i input.css -o output.css --minify
EOF

# Jalankan build Docker
echo "🔨 Building..."
docker build -f Dockerfile.tailwind -t tailwind-css-builder .

# Ekstrak hasil
echo "📦 Extracting built Tailwind CSS..."
docker run --rm tailwind-css-builder cat /build/output.css > static/css/tailwind.css

# Cleanup
rm Dockerfile.tailwind

# Verifikasi hasil
if [ $? -eq 0 ] && [ -s static/css/tailwind.css ]; then
    echo "✅ Tailwind CSS berhasil dibangun!"
    echo "📄 Output file: static/css/tailwind.css"
    echo "📏 File size: $(du -h static/css/tailwind.css | cut -f1)"
else
    echo "❌ Gagal membangun Tailwind CSS."
    exit 1
fi
