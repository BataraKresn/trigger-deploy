#!/bin/bash
# =================================
# Development Helper Script
# =================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

show_help() {
    echo "🔧 Trigger Deploy - Development Helper"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  start       Start the application"
    echo "  test        Run tests"
    echo "  build       Build Docker image"
    echo "  up          Start with Docker Compose"
    echo "  down        Stop Docker Compose"
    echo "  update      Update Docker service"
    echo "  logs        Show application logs"
    echo "  clean       Cleanup old files and logs"
    echo "  install     Install dependencies"
    echo "  lint        Run code linting (if available)"
    echo "  help        Show this help"
    echo
}

case "${1:-help}" in
    "start")
        echo "🚀 Starting Trigger Deploy Server..."
        python app.py
        ;;
    "test")
        echo "🧪 Running tests..."
        cd tests && python test_app.py
        ;;
    "build")
        echo "🏗️ Building Docker image..."
        docker compose build
        ;;
    "up")
        echo "🐳 Starting with Docker Compose..."
        docker compose up -d
        echo "✅ Service started! Check: http://localhost:5000"
        ;;
    "down")
        echo "🛑 Stopping Docker Compose..."
        docker compose down
        ;;
    "update")
        echo "♻️ Updating Docker service..."
        ./scripts/update-docker.sh
        ;;
    "logs")
        echo "📋 Showing application logs..."
        if [ -f "logs/app.log" ]; then
            tail -f logs/app.log
        else
            echo "No application logs found."
        fi
        ;;
    "clean")
        echo "🧹 Cleaning up..."
        ./scripts/cleanup.sh
        ;;
    "install")
        echo "📦 Installing dependencies..."
        pip install -r requirements.txt
        ;;
    "lint")
        echo "🔍 Running linting..."
        if command -v flake8 &> /dev/null; then
            flake8 src/ app.py wsgi.py
        else
            echo "flake8 not installed. Install with: pip install flake8"
        fi
        ;;
    "help"|*)
        show_help
        ;;
esac
