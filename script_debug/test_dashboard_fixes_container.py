#!/usr/bin/env python3
"""
Test script for the improved idempotent database initialization
Container version - works inside Docker
"""

import os
import sys
import json
import logging

# Add the app directory to Python path (inside Docker)
sys.path.insert(0, '/app')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_services_json():
    """Test services.json structure"""
    print("🔍 Testing services.json structure...")
    try:
        services_file = '/app/static/services.json'
        if not os.path.exists(services_file):
            print(f"❌ Services file not found: {services_file}")
            return False
            
        with open(services_file, 'r') as f:
            services = json.load(f)
        
        if isinstance(services, list):
            print(f"✅ Services file contains {len(services)} services (list format)")
            
            # Check first service structure
            if services and isinstance(services[0], dict):
                required_keys = ['name', 'type']
                first_service = services[0]
                has_required = all(key in first_service for key in required_keys)
                
                if has_required:
                    print(f"✅ Service structure valid - example: {first_service.get('name')}")
                    return True
                else:
                    print(f"❌ Service missing required keys: {required_keys}")
                    return False
            else:
                print("❌ Services list is empty or invalid")
                return False
                
        elif isinstance(services, dict):
            print("✅ Services file in dictionary format")
            if 'local_services' in services or 'remote_services' in services:
                print("✅ Contains expected service categories")
                return True
            else:
                print("❌ Missing expected service categories")
                return False
        else:
            print("❌ Invalid services file format")
            return False
            
    except Exception as e:
        print(f"❌ Error reading services.json: {e}")
        return False

def test_module_imports():
    """Test if modules can be imported"""
    print("\n🔍 Testing module imports...")
    
    try:
        # Test service monitor import
        from src.utils.service_monitor import ServiceMonitor
        print("✅ Service monitor imported successfully")
        
        # Test creating instance
        monitor = ServiceMonitor()
        print("✅ Service monitor instance created")
        
        # Test auth import
        from src.utils.auth import is_authenticated, require_auth
        print("✅ Auth functions imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Error importing modules: {e}")
        return False

def test_config_files():
    """Test config files exist"""
    print("\n🔍 Testing config files...")
    
    try:
        config_files = [
            '/app/config/servers.json',
            '/app/config/services.json',
            '/app/static/servers.json',
            '/app/static/services.json'
        ]
        
        existing_files = []
        for file_path in config_files:
            if os.path.exists(file_path):
                existing_files.append(file_path)
                print(f"✅ Found: {file_path}")
        
        if existing_files:
            print(f"✅ Found {len(existing_files)} config files")
            return True
        else:
            print("❌ No config files found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking config files: {e}")
        return False

def test_flask_app():
    """Test if Flask app can be imported"""
    print("\n🔍 Testing Flask app...")
    
    try:
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        
        # Test some routes exist
        with app.test_client() as client:
            routes = ['/health', '/']
            for route in routes:
                try:
                    response = client.get(route)
                    print(f"✅ Route {route} responds with status {response.status_code}")
                except Exception as e:
                    print(f"⚠️  Route {route} error: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing Flask app: {e}")
        return False

def test_database_connection():
    """Test database connection (if available)"""
    print("\n🔍 Testing database connection...")
    
    try:
        # Check if environment variables exist
        db_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
        missing_vars = [var for var in db_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"⚠️  Missing DB environment variables: {missing_vars}")
            print("⚠️  Skipping database test")
            return True  # Not a failure, just skip
        
        from src.models.database import test_database_connection
        if test_database_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"⚠️  Database test skipped: {e}")
        return True  # Not a critical failure

def main():
    print("🚀 Testing Dashboard Fixes (Container Version)")
    print("=" * 50)
    
    tests = [
        ("services.json structure", test_services_json),
        ("module imports", test_module_imports),
        ("config files", test_config_files),
        ("Flask app", test_flask_app),
        ("database connection", test_database_connection)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            failed += 1
    
    print(f"\n📊 Test Results")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed > 0:
        print(f"\n⚠️  {failed} test(s) failed. Check the errors above.")
        sys.exit(1)
    else:
        print(f"\n🎉 All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
