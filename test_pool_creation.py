#!/usr/bin/env python3
"""
Test Database Pool Creation
Simulate the exact process that happens in the application
"""

import os
import sys
import logging

# Setup logging like the application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

def test_full_initialization():
    """Test the complete database initialization process"""
    logger.info("🚀 Testing Full Database Initialization")
    logger.info("=" * 60)
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Import the exact same way as the application
        from models.database import get_db_manager, init_database
        
        logger.info("Step 1: Testing get_db_manager()...")
        db_manager = get_db_manager()
        
        if db_manager:
            logger.info("✅ get_db_manager() successful")
            logger.info(f"  Manager: {db_manager}")
            logger.info(f"  Pool: {db_manager.pool}")
            logger.info(f"  Initialized: {db_manager._initialized}")
            
            # Test health check
            logger.info("Step 2: Testing health check...")
            if db_manager.health_check():
                logger.info("✅ Health check passed")
            else:
                logger.warning("⚠️  Health check failed")
        else:
            logger.error("❌ get_db_manager() returned None")
            return False
        
        logger.info("Step 3: Testing init_database()...")
        if init_database():
            logger.info("✅ init_database() successful")
        else:
            logger.error("❌ init_database() failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Full initialization failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Import traceback for detailed error
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        
        return False

def test_manual_connection():
    """Test manual connection using the same parameters"""
    logger.info("\n🔍 Testing Manual Connection")
    logger.info("=" * 50)
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Get config the same way
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from models.config import config
        
        conn_params = {
            'host': config.POSTGRES_HOST,
            'port': config.POSTGRES_PORT,
            'database': config.POSTGRES_DB,
            'user': config.POSTGRES_USER,
            'password': config.POSTGRES_PASSWORD,
            'cursor_factory': RealDictCursor,
            'connect_timeout': 10,
            'application_name': 'trigger_deploy_test'
        }
        
        # Add SSL config
        ssl_config = config.get_postgres_ssl_config()
        conn_params.update(ssl_config)
        
        logger.info(f"Connection parameters:")
        safe_params = {k: v for k, v in conn_params.items() if k != 'password'}
        logger.info(f"  {safe_params}")
        
        # Test single connection
        logger.info("Testing single connection...")
        conn = psycopg2.connect(**conn_params)
        
        cursor = conn.cursor()
        cursor.execute('SELECT version()')
        version = cursor.fetchone()[0]
        logger.info(f"✅ Single connection successful")
        logger.info(f"  Version: {version[:80]}...")
        
        cursor.close()
        conn.close()
        
        # Test connection pool
        logger.info("Testing connection pool...")
        from psycopg2 import pool
        
        test_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            **conn_params
        )
        
        logger.info("✅ Connection pool created successfully")
        
        # Test getting connection from pool
        pool_conn = test_pool.getconn()
        cursor = pool_conn.cursor()
        cursor.execute('SELECT current_database()')
        db_name = cursor.fetchone()[0]
        logger.info(f"✅ Pool connection successful, database: {db_name}")
        
        cursor.close()
        test_pool.putconn(pool_conn)
        test_pool.closeall()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Manual connection failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

def main():
    """Main test function"""
    logger.info("🧪 Database Pool Creation Test")
    logger.info("=" * 60)
    
    # Test 1: Manual connection 
    manual_success = test_manual_connection()
    
    # Test 2: Full initialization
    full_success = test_full_initialization()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Summary:")
    logger.info(f"  Manual Connection: {'✅ OK' if manual_success else '❌ FAILED'}")
    logger.info(f"  Full Initialization: {'✅ OK' if full_success else '❌ FAILED'}")
    
    if manual_success and full_success:
        logger.info("\n🎉 All tests passed! Database initialization should work in the application.")
        return 0
    elif manual_success and not full_success:
        logger.info(f"\n⚠️  Manual connection works but full initialization fails.")
        logger.info("This suggests an issue in the application's database initialization code.")
        return 1
    else:
        logger.info(f"\n❌ Connection problems detected.")
        return 1

if __name__ == '__main__':
    exit(main())
