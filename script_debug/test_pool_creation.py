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
        src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
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
        src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
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
        
        # Add SSL config with error handling
        try:
            ssl_config = config.get_postgres_ssl_config()
            conn_params.update(ssl_config)
        except Exception as ssl_error:
            logger.warning(f"SSL config error: {ssl_error}, using defaults")
            conn_params['sslmode'] = 'disable'
        
        logger.info(f"Connection parameters:")
        safe_params = {k: v for k, v in conn_params.items() if k != 'password'}
        logger.info(f"  {safe_params}")
        
        # Validate parameters before connection
        for param_name, param_value in conn_params.items():
            if param_value is None:
                logger.error(f"Parameter '{param_name}' is None")
                return False
            if param_name in ['host', 'database', 'user', 'password'] and not str(param_value).strip():
                logger.error(f"Parameter '{param_name}' is empty")
                return False
        
        # Test single connection
        logger.info("Testing single connection...")
        conn = psycopg2.connect(**conn_params)
        
        cursor = conn.cursor()
        cursor.execute('SELECT version()')
        result = cursor.fetchone()
        
        if not result or len(result) == 0:
            logger.error("Empty result from version query")
            return False
            
        version = result[0] if result and len(result) > 0 else "Unknown"
        logger.info(f"✅ Single connection successful")
        logger.info(f"  Version: {version[:80]}...")
        
        cursor.close()
        conn.close()
        
        # Test connection pool
        logger.info("Testing connection pool...")
        from psycopg2 import pool
        
        # Create pool with explicit error handling
        try:
            test_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=5,
                **conn_params
            )
            
            if not test_pool:
                logger.error("ThreadedConnectionPool returned None")
                return False
                
        except KeyError as ke:
            logger.error(f"KeyError creating pool: {ke}")
            logger.error(f"Missing connection parameter: {ke}")
            logger.error(f"Available parameters: {list(conn_params.keys())}")
            return False
        except Exception as pool_error:
            logger.error(f"Pool creation error: {pool_error}")
            logger.error(f"Error type: {type(pool_error).__name__}")
            if hasattr(pool_error, 'args'):
                logger.error(f"Error args: {pool_error.args}")
            return False
        
        logger.info("✅ Connection pool created successfully")
        
        # Test getting connection from pool
        try:
            pool_conn = test_pool.getconn()
            if not pool_conn:
                logger.error("Failed to get connection from pool")
                return False
                
            cursor = pool_conn.cursor()
            cursor.execute('SELECT current_database()')
            result = cursor.fetchone()
            
            if not result or len(result) == 0:
                logger.error("Empty result from database query")
                return False
                
            db_name = result[0] if result and len(result) > 0 else "Unknown"
            logger.info(f"✅ Pool connection successful, database: {db_name}")
            
            cursor.close()
            test_pool.putconn(pool_conn)
            test_pool.closeall()
            
        except Exception as pool_test_error:
            logger.error(f"Pool test error: {pool_test_error}")
            try:
                test_pool.closeall()
            except:
                pass
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Manual connection failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        if hasattr(e, 'args'):
            logger.error(f"Error args: {e.args}")
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
