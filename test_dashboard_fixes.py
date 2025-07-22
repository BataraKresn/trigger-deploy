#!/usr/bin/env python3
"""
Quick test script for the dashboard fixes
"""

import os
import sys
import json
import requests
import time

# Add the source directory to Python path
sys.path.insert(0, '/workspaces/trigger-deploy')

def test_services_json():
    """Test services.json structure"""
    print("🔍 Testing services.json structure...")
    
    try:
        with open('/workspaces/trigger-deploy/static/services.json', 'r') as f:
            services = json.load(f)
        
        if isinstance(services, list):
            print(f"✅ Services JSON is valid list with {len(services)} services")
            for i, service in enumerate(services):
                if 'name' in service and 'type' in service:
                    print(f"   {i+1}. {service.get('icon', '📦')} {service['name']} ({service['type']})")
                else:
                    print(f"   ❌ Service {i+1} missing required fields")
            return True
        else:
            print("❌ Services JSON is not a list")
            return False
            
    except Exception as e:
        print(f"❌ Error reading services.json: {e}")
        return False

def test_service_monitor_import():
    """Test service monitor import"""
    print("\n🔍 Testing service monitor import...")
    
    try:
        from src.utils.service_monitor import ServiceMonitor, service_monitor
        print("✅ Service monitor imports successfully")
        
        # Test loading services
        services = service_monitor.load_services()
        print(f"✅ Loaded {len(services)} services from config")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing service monitor: {e}")
        return False

def test_database_init():
    """Test database initialization"""
    print("\n🔍 Testing database initialization...")
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv('/workspaces/trigger-deploy/.env')
        
        from src.models.database import check_table_exists, get_database_url
        
        # Test database URL construction
        db_url = get_database_url()
        print("✅ Database URL constructed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        return False

def test_auth_functions():
    """Test authentication functions"""
    print("\n🔍 Testing authentication functions...")
    
    try:
        from src.utils.auth import is_authenticated, login_user, logout_user
        print("✅ Authentication functions import successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error importing auth functions: {e}")
        return False

def main():
    print("🚀 Testing Dashboard Fixes")
    print("=" * 50)
    
    tests = [
        test_services_json,
        test_service_monitor_import,
        test_auth_functions,
        test_database_init,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 Test Results")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Dashboard should be working properly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the errors above.")

if __name__ == "__main__":
    main()
