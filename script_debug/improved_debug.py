#!/usr/bin/env python3
"""
Improved debug script for database connection issues
"""

import os
import sys
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables"""
    logger.info("🔍 Checking Environment Variables")
    logger.info("=" * 50)
    
    required_vars = [
        'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 
        'POSTGRES_USER', 'POSTGRES_PASSWORD', 'DATABASE_URL'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                logger.info(f"  ✅ {var}: ****** (set)")
            else:
                logger.info(f"  ✅ {var}: {value}")
        else:
            logger.error(f"  ❌ {var}: Not set")
            missing.append(var)
    
    return len(missing) == 0

def test_direct_connection():
    """Test direct psycopg2 connection"""
    logger.info("\n🔍 Testing Direct psycopg2 Connection")
    logger.info("=" * 50)
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Get connection parameters from environment
        conn_params = {
            'host': os.getenv('POSTGRES_HOST'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'connect_timeout': 10
        }
        
        logger.info(f"Connection params: {dict(conn_params, password='***')}")
        
        # Test without RealDictCursor first
        logger.info("Testing with regular cursor...")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute('SELECT version()')
        result = cursor.fetchone()
        logger.info(f"✅ Regular cursor result: {result[0][:50]}...")
        cursor.close()
        conn.close()
        
        # Test with RealDictCursor
        logger.info("Testing with RealDictCursor...")
        conn_params['cursor_factory'] = RealDictCursor
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute('SELECT version() as db_version')
        result = cursor.fetchone()
        logger.info(f"✅ RealDictCursor result: {result.get('db_version', 'N/A')[:50]}...")
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct connection failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def test_application_imports():
    """Test importing application modules"""
    logger.info("\n🔍 Testing Application Imports")
    logger.info("=" * 50)
    
    try:
        # Add src to Python path
        script_dir = os.path.dirname(__file__)
        src_path = os.path.join(os.path.dirname(script_dir), 'src')
        
        if not os.path.exists(src_path):
            logger.error(f"❌ Source path does not exist: {src_path}")
            return False
            
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            logger.info(f"Added to Python path: {src_path}")
        
        # Test config import
        try:
            from models.config import config
            logger.info("✅ Config import successful")
            logger.info(f"  Database URL present: {'Yes' if config.DATABASE_URL else 'No'}")
            logger.info(f"  Host: {config.POSTGRES_HOST}")
            logger.info(f"  Port: {config.POSTGRES_PORT}")
            logger.info(f"  Database: {config.POSTGRES_DB}")
        except Exception as e:
            logger.error(f"❌ Config import failed: {e}")
            return False
        
        # Test database import
        try:
            from models.database import PostgreSQLManager
            logger.info("✅ Database module import successful")
        except Exception as e:
            logger.error(f"❌ Database import failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def test_manager_creation():
    """Test creating PostgreSQL manager"""
    logger.info("\n🔍 Testing PostgreSQL Manager Creation")
    logger.info("=" * 50)
    
    try:
        from models.database import PostgreSQLManager
        
        logger.info("Creating PostgreSQLManager...")
        manager = PostgreSQLManager()
        logger.info("✅ Manager created successfully")
        
        logger.info(f"Manager details:")
        logger.info(f"  Host: {getattr(manager, 'host', 'N/A')}")
        logger.info(f"  Port: {getattr(manager, 'port', 'N/A')}")
        logger.info(f"  Database: {getattr(manager, 'database', 'N/A')}")
        logger.info(f"  User: {getattr(manager, 'user', 'N/A')}")
        
        # Try initialization
        logger.info("Attempting initialization...")
        try:
            manager.initialize()
            logger.info("✅ Manager initialization successful")
            
            # Try a simple health check
            if hasattr(manager, 'health_check'):
                logger.info("Testing health check...")
                health_ok = manager.health_check()
                logger.info(f"Health check result: {'✅ PASS' if health_ok else '❌ FAIL'}")
            
            return True
            
        except Exception as init_error:
            logger.error(f"❌ Manager initialization failed: {init_error}")
            logger.error(f"Error type: {type(init_error).__name__}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Manager creation failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def main():
    """Main diagnostic function"""
    logger.info("🚀 Improved Database Diagnostic")
    logger.info("=" * 60)
    
    # Test 1: Environment
    env_ok = check_environment()
    
    # Test 2: Direct connection
    direct_ok = test_direct_connection()
    
    # Test 3: Application imports
    imports_ok = test_application_imports()
    
    # Test 4: Manager creation
    manager_ok = test_manager_creation()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Diagnostic Summary:")
    logger.info(f"  Environment:      {'✅ OK' if env_ok else '❌ FAILED'}")
    logger.info(f"  Direct Connection: {'✅ OK' if direct_ok else '❌ FAILED'}")
    logger.info(f"  Application Imports: {'✅ OK' if imports_ok else '❌ FAILED'}")
    logger.info(f"  Manager Creation:  {'✅ OK' if manager_ok else '❌ FAILED'}")
    
    all_ok = all([env_ok, direct_ok, imports_ok, manager_ok])
    
    if all_ok:
        logger.info("\n🎉 All diagnostics passed!")
        return 0
    else:
        logger.info("\n⚠️  Some diagnostics failed. Check the logs above.")
        return 1

if __name__ == '__main__':
    exit(main())
