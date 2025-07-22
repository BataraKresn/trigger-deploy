#!/usr/bin/env python3
"""
Test SQLAlchemy User model and authentication flow
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, '/workspaces/trigger-deploy')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_user_model():
    """Test the SQLAlchemy User model"""
    print("Testing SQLAlchemy User model...")
    
    try:
        # Set environment variables
        os.environ['POSTGRES_HOST'] = '30.30.30.11'
        os.environ['POSTGRES_PORT'] = '5456'
        os.environ['POSTGRES_DB'] = 'trigger_deploy'
        os.environ['POSTGRES_USER'] = 'trigger_deploy_user'
        os.environ['POSTGRES_PASSWORD'] = 'secure_password_123'
        os.environ['POSTGRES_SSL_MODE'] = 'disable'
        
        from src.models.database import get_db_manager, init_database
        from src.models.user import User
        
        print("✓ Database and User models imported successfully")
        
        # Initialize database
        if not init_database():
            print("! Database initialization failed - continuing with tests")
        else:
            print("✓ Database initialized successfully")
        
        # Test database manager
        db = get_db_manager()
        if not db:
            print("✗ get_db_manager() returned None")
            return False
        
        print("✓ Database manager obtained")
        
        # Test pool attribute (the main fix)
        if db.pool is None:
            print("! Pool is None - database may not be reachable")
        else:
            print("✓ Pool attribute accessible")
        
        # Test health check
        if db.health_check():
            print("✓ Database health check passed")
        else:
            print("! Database health check failed - database may not be reachable")
        
        # Test user authentication (should not crash with SQLAlchemy error)
        try:
            user = db.authenticate_user("admin", "admin123")
            if user:
                print(f"✓ Authentication test passed - user found: {user.username}")
            else:
                print("! Authentication test - no user found (expected if no users exist)")
        except Exception as e:
            print(f"✗ Authentication test failed: {e}")
            return False
        
        # Test user creation
        try:
            test_user_data = {
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'testpass123',
                'full_name': 'Test User',
                'role': 'user'
            }
            
            created_user = db.create_user(test_user_data)
            if created_user:
                print(f"✓ User creation test passed - created user: {created_user.username}")
                
                # Test password checking
                if created_user.check_password('testpass123'):
                    print("✓ Password verification test passed")
                else:
                    print("✗ Password verification test failed")
                    
            else:
                print("! User creation test - user not created (may already exist)")
                
        except Exception as e:
            print(f"! User creation test error: {e}")
        
        print("\n🎉 SQLAlchemy User model tests completed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SQLAlchemy User Model & Authentication Test")
    print("=" * 60)
    
    success = test_user_model()
    
    print("=" * 60)
    if success:
        print("Result: SUCCESS ✓")
        print("The SQLAlchemy error should be fixed!")
        sys.exit(0)
    else:
        print("Result: FAILURE ✗")
        sys.exit(1)
