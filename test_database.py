#!/usr/bin/env python3
"""
Test script for database.py module
Run this to verify the database configuration is working properly.
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, '/workspaces/trigger-deploy')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file (if available)
try:
    from dotenv import load_dotenv
    load_dotenv('/workspaces/trigger-deploy/.env')
    print("✓ Environment variables loaded from .env file")
except ImportError:
    print("! python-dotenv not available, using system environment variables")
except FileNotFoundError:
    print("! .env file not found, using system environment variables")

def test_database_module():
    """Test the database module functionality."""
    print("Testing database module...")
    
    try:
        # Import the database module
        from src.models.database import (
            init_database, 
            close_database, 
            get_engine, 
            get_session,
            test_database_connection,
            db_manager
        )
        print("✓ Database module imported successfully")
        
        # Check environment variables
        required_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
            print("Please set these environment variables or create a .env file")
            return False
        
        print("✓ Required environment variables are set")
        
        # Test database initialization
        print("Initializing database...")
        if init_database():
            print("✓ Database initialized successfully")
        else:
            print("✗ Database initialization failed")
            return False
        
        # Test engine access
        try:
            engine = get_engine()
            print(f"✓ Engine obtained: {type(engine)}")
        except Exception as e:
            print(f"✗ Failed to get engine: {e}")
            return False
        
        # Test session creation
        try:
            session = get_session()
            session.close()
            print("✓ Session created and closed successfully")
        except Exception as e:
            print(f"✗ Failed to create session: {e}")
            return False
        
        # Test database manager (backward compatibility)
        try:
            if db_manager.test_connection():
                print("✓ Database manager connection test passed")
            else:
                print("✗ Database manager connection test failed")
                return False
        except Exception as e:
            print(f"✗ Database manager test failed: {e}")
            return False
        
        # Clean up
        close_database()
        print("✓ Database connections closed")
        
        print("\n🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Database Module Test")
    print("=" * 50)
    
    success = test_database_module()
    
    print("=" * 50)
    if success:
        print("Result: SUCCESS ✓")
        sys.exit(0)
    else:
        print("Result: FAILURE ✗")
        sys.exit(1)
