#!/bin/bash

# Deploy Server Initialization Script
# This script initializes the database and sets up the application

echo "🚀 Initializing Deploy Server..."

# Create logs directory
mkdir -p logs

# Export environment variables
export FLASK_APP=app.py
export FLASK_ENV=production

echo "📊 Initializing database..."

# Initialize database migration
flask db init 2>/dev/null || echo "Database already initialized"

# Create migration
flask db migrate -m "Initial migration with all models" 2>/dev/null || echo "Migration already exists"

# Apply migration
flask db upgrade

echo "👤 Creating default admin user..."

# Create default admin user using Python script
python3 << EOF
import os
import sys
sys.path.append('.')

try:
    from app import app
    from models import db
    from models.user import User
    
    with app.app_context():
        # Check if admin user exists
        admin_user = User.find_by_username('admin')
        if not admin_user:
            admin_user = User.create_user(
                username='admin',
                password='admin123',
                email='admin@deployserver.local',
                role='admin'
            )
            print("✅ Admin user created: admin/admin123")
        else:
            print("ℹ️  Admin user already exists")
        
        # Create demo user
        demo_user = User.find_by_username('demo')
        if not demo_user:
            demo_user = User.create_user(
                username='demo',
                password='demo123',
                email='demo@deployserver.local',
                role='user'
            )
            print("✅ Demo user created: demo/demo123")
        else:
            print("ℹ️  Demo user already exists")

except Exception as e:
    print(f"❌ Error creating users: {e}")
    import traceback
    traceback.print_exc()
EOF

echo "🗂️  Creating sample servers..."

# Create sample servers
python3 << EOF
import os
import sys
sys.path.append('.')

try:
    from app import app
    from models import db
    from models.server import Server
    from models.user import User
    
    with app.app_context():
        # Get admin user
        admin_user = User.find_by_username('admin')
        
        # Sample servers
        sample_servers = [
            {
                'ip': '192.168.1.100',
                'alias': 'web-prod',
                'name': 'Production Web Server',
                'user': 'deploy',
                'script_path': '/opt/deploy/web-deploy.sh',
                'description': 'Main production web server',
                'environment': 'production'
            },
            {
                'ip': '192.168.1.101',
                'alias': 'api-prod',
                'name': 'Production API Server',
                'user': 'deploy',
                'script_path': '/opt/deploy/api-deploy.sh',
                'description': 'Production API backend server',
                'environment': 'production'
            },
            {
                'ip': '192.168.1.102',
                'alias': 'web-staging',
                'name': 'Staging Web Server',
                'user': 'deploy',
                'script_path': '/opt/deploy/web-deploy.sh',
                'description': 'Staging environment web server',
                'environment': 'staging'
            }
        ]
        
        for server_data in sample_servers:
            existing_server = Server.find_by_alias(server_data['alias'])
            if not existing_server:
                server = Server.create_server(
                    created_by=admin_user.id if admin_user else None,
                    **server_data
                )
                print(f"✅ Created server: {server.alias} ({server.ip})")
            else:
                print(f"ℹ️  Server already exists: {server_data['alias']}")

except Exception as e:
    print(f"❌ Error creating sample servers: {e}")
    import traceback
    traceback.print_exc()
EOF

echo "🎉 Initialization completed!"
echo ""
echo "📋 Summary:"
echo "  - Database initialized and migrated"
echo "  - Admin user: admin/admin123"
echo "  - Demo user: demo/demo123"
echo "  - Sample servers created"
echo ""
echo "🚀 You can now start the application:"
echo "  python app.py"
echo ""
echo "📖 API Documentation available at:"
echo "  http://localhost:5001/docs/"
echo ""
echo "💡 Frontend should connect to:"
echo "  http://localhost:5001/api"
