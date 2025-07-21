#!/bin/bash
# Script untuk test integrasi semua komponen

set -e

echo "🧪 Testing Trigger Deploy Integration"
echo "===================================="

# Use virtual environment if available
PYTHON_CMD="python3"
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    echo "✅ Using virtual environment"
fi

# Test 1: Configuration
echo "1️⃣ Testing Configuration..."
$PYTHON_CMD -c "
import sys
sys.path.insert(0, 'src')
from src.models.config import config
print('✅ Config loaded successfully')
print(f'   Database URL: {config.DATABASE_URL}')
print(f'   JWT Secret: {config.JWT_SECRET[:10]}...')
print(f'   Admin User: {config.DEFAULT_ADMIN_USERNAME}')
"

# Test 2: Database imports
echo "2️⃣ Testing Database Module..."
$PYTHON_CMD -c "
import sys
sys.path.insert(0, 'src')
from src.models.database import PostgreSQLManager, User
print('✅ Database module imported successfully')
"

# Test 3: Routes imports
echo "3️⃣ Testing Routes..."
$PYTHON_CMD -c "
import sys
sys.path.insert(0, 'src')
from src.routes.user_postgres import user_bp
from src.routes.main import main_bp
from src.routes.api import api_bp
from src.routes.deploy import deploy_bp
print('✅ All routes imported successfully')
"

# Test 4: App creation
echo "4️⃣ Testing App Creation..."
$PYTHON_CMD -c "
import sys
sys.path.insert(0, '.')
from app import create_app
app = create_app()
print('✅ App created successfully')
print(f'   Blueprints: {[bp.name for bp in app.blueprints.values()]}')
"

# Test 5: Dependencies check
echo "5️⃣ Testing Dependencies..."
$PYTHON_CMD -c "
import flask
import flask_cors
import asyncpg
import jwt
import psutil
import requests
print('✅ All required dependencies available')
"

echo ""
echo "🎉 All integration tests passed!"
echo "✅ Your application is ready to run"
echo ""
echo "Next steps:"
echo "  1. Start the database: docker compose up postgres -d"
echo "  2. Wait for PostgreSQL to be ready (about 30 seconds)"
echo "  3. Run the app: python app.py"
echo "  4. Or start everything: docker compose up -d"
