#!/bin/bash
# Build script untuk generate Tailwind CSS

echo "🎨 Building Tailwind CSS..."

# Check if Node.js dan npm tersedia
if ! command -v npm &> /dev/null; then
    echo "❌ npm tidak ditemukan. Install Node.js terlebih dahulu."
    echo "Atau gunakan Docker build yang sudah include Tailwind build."
    exit 1
fi

# Install tailwindcss jika belum ada
if ! command -v tailwindcss &> /dev/null; then
    echo "📦 Installing Tailwind CSS CLI..."
    npm install -g tailwindcss
fi

# Build CSS
echo "⚡ Generating optimized CSS..."
tailwindcss -i static/css/input.css -o static/css/tailwind.css --minify

if [ $? -eq 0 ]; then
    echo "✅ Tailwind CSS berhasil di-build!"
    echo "📄 Output: static/css/tailwind.css"
else
    echo "❌ Build gagal!"
    exit 1
fi
