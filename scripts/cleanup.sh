#!/bin/bash
# =================================
# Cleanup Script - Clean Development Environment
# =================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🧹 Cleaning up Trigger Deploy..."

# Function to show menu
show_menu() {
    echo
    echo "Select cleanup options:"
    echo "1) Python cache files (__pycache__, *.pyc)"
    echo "2) Log files (trim to last 50 lines)"
    echo "3) Old trigger logs (keep last 10)"
    echo "4) Temporary files (*.tmp, .DS_Store)"
    echo "5) Docker resources (images, containers)"
    echo "6) All of the above"
    echo "0) Exit"
    echo
}

# Clean Python cache
clean_python_cache() {
    echo "🐍 Removing Python cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    echo "  ✅ Python cache cleaned"
}

# Clean logs
clean_logs() {
    echo "📋 Cleaning log files..."
    if [ -d "logs" ]; then
        for log_file in logs/*.log; do
            if [ -f "$log_file" ]; then
                echo "  Trimming $(basename "$log_file")..."
                tail -n 50 "$log_file" > "${log_file}.tmp" && mv "${log_file}.tmp" "$log_file"
            fi
        done
        echo "  ✅ Log files trimmed to last 50 lines"
    else
        echo "  ℹ️  No logs directory found"
    fi
}

# Clean old trigger logs
clean_trigger_logs() {
    echo "🔄 Cleaning old trigger logs..."
    if [ -d "trigger-logs" ]; then
        cd trigger-logs
        log_count=$(ls -1 trigger-*.log 2>/dev/null | wc -l)
        if [ "$log_count" -gt 10 ]; then
            ls -t trigger-*.log | tail -n +11 | xargs rm -f 2>/dev/null || true
            echo "  ✅ Removed $((log_count - 10)) old trigger logs"
        else
            echo "  ℹ️  Less than 10 trigger logs, keeping all"
        fi
        cd ..
    else
        echo "  ℹ️  No trigger-logs directory found"
    fi
}

# Clean temporary files
clean_temp_files() {
    echo "🗑️  Removing temporary files..."
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name ".DS_Store" -delete 2>/dev/null || true
    find . -name "*.swp" -delete 2>/dev/null || true
    find . -name "*.swo" -delete 2>/dev/null || true
    echo "  ✅ Temporary files removed"
}

# Clean Docker resources
clean_docker() {
    echo "🐳 Cleaning Docker resources..."
    if command -v docker &> /dev/null; then
        docker system prune -f 2>/dev/null || true
        echo "  ✅ Docker resources cleaned"
    else
        echo "  ℹ️  Docker not available"
    fi
}

# Clean all
clean_all() {
    clean_python_cache
    clean_logs
    clean_trigger_logs
    clean_temp_files
    clean_docker
}
# Main menu loop
if [ $# -eq 0 ]; then
    while true; do
        show_menu
        read -p "Choose option (0-6): " choice
        
        case $choice in
            1) clean_python_cache ;;
            2) clean_logs ;;
            3) clean_trigger_logs ;;
            4) clean_temp_files ;;
            5) clean_docker ;;
            6) clean_all ;;
            0) echo "👋 Goodbye!"; break ;;
            *) echo "❌ Invalid option. Please try again." ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
else
    # Command line arguments
    case "$1" in
        "cache") clean_python_cache ;;
        "logs") clean_logs ;;
        "trigger") clean_trigger_logs ;;
        "temp") clean_temp_files ;;
        "docker") clean_docker ;;
        "all") clean_all ;;
        *) 
            echo "Usage: $0 [cache|logs|trigger|temp|docker|all]"
            exit 1
            ;;
    esac
fi

echo
echo "📊 Current disk usage:"
du -sh . 2>/dev/null || true

echo "✅ Cleanup completed!"
