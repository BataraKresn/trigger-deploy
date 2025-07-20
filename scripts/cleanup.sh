#!/bin/bash
# =================================
# Cleanup Script - Remove Old Files
# =================================

echo "🧹 Starting cleanup of old files..."

# List of files that are no longer needed
OLD_FILES=(
    "app.py"                    # Replaced by app_new.py
    "deployment_history.py"     # Functionality moved to src/
    "service_monitor.py"        # Functionality moved to src/
    "test_app.py"              # Will be replaced by proper tests
    "home_backup.html"         # Backup file no longer needed
)

# Function to backup file before deletion
backup_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo "📦 Backing up $file..."
        mkdir -p "backup/$(date +%Y%m%d)"
        cp "$file" "backup/$(date +%Y%m%d)/"
    fi
}

# Function to remove file
remove_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo "🗑️  Removing $file..."
        rm "$file"
    else
        echo "ℹ️  File $file not found, skipping..."
    fi
}

# Create backup directory
mkdir -p backup

echo "📋 Files to be cleaned up:"
for file in "${OLD_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file (exists)"
    else
        echo "  ❌ $file (not found)"
    fi
done

# Ask for confirmation
read -p "🤔 Do you want to proceed with cleanup? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Proceeding with cleanup..."
    
    # Backup and remove old files
    for file in "${OLD_FILES[@]}"; do
        backup_file "$file"
        remove_file "$file"
    done
    
    # Clean up empty __pycache__ directories
    echo "🧹 Cleaning up __pycache__ directories..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    echo "✅ Cleanup completed!"
    echo "📦 Backups saved in backup/$(date +%Y%m%d)/"
else
    echo "❌ Cleanup cancelled."
fi

echo "🏁 Cleanup script finished."
