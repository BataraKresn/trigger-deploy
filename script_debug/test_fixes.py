#!/usr/bin/env python3
"""
Test script to verify database fixes
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if imports work correctly"""
    logger.info("🔍 Testing Imports")
    logger.info("=" * 50)
    
    try:
        # Add src to path
        src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            
        logger.info(f"Added to sys.path: {src_path}")
        
        # Test config import
        try:
            from models.config import config
            logger.info("✅ Config import successful")
            logger.info(f"  Database URL: {'***@***' if config.DATABASE_URL else 'Not set'}")
        except Exception as e:
            logger.error(f"❌ Config import failed: {e}")
            return False
        
        # Test database import
        try:
            from models.database import PostgreSQLManager, get_db_manager
            logger.info("✅ Database import successful")
        except Exception as e:
            logger.error(f"❌ Database import failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        return False

def test_database_creation():
    """Test database manager creation"""
    logger.info("\n🔍 Testing Database Manager Creation")
    logger.info("=" * 50)
    
    try:
        from models.database import PostgreSQLManager
        
        logger.info("Creating PostgreSQLManager instance...")
        manager = PostgreSQLManager()
        logger.info("✅ PostgreSQLManager created successfully")
        logger.info(f"  Manager: {manager}")
        logger.info(f"  Host: {getattr(manager, 'host', 'Not set')}")
        logger.info(f"  Port: {getattr(manager, 'port', 'Not set')}")
        logger.info(f"  Database: {getattr(manager, 'database', 'Not set')}")
        
        # Test initialization
        logger.info("Testing manager initialization...")
        try:
            manager.initialize()
            logger.info("✅ Manager initialization successful")
            return True
        except Exception as init_error:
            logger.error(f"❌ Initialization failed: {init_error}")
            logger.error(f"Error type: {type(init_error).__name__}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Failed to create PostgreSQLManager: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

def main():
    """Main test function"""
    logger.info("🚀 Database Fixes Test")
    logger.info("=" * 60)
    
    # Test 1: Imports
    imports_ok = test_imports()
    
    # Test 2: Database creation
    db_creation_ok = test_database_creation()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Summary:")
    logger.info(f"  Imports:          {'✅ OK' if imports_ok else '❌ FAILED'}")
    logger.info(f"  Database Creation: {'✅ OK' if db_creation_ok else '❌ FAILED'}")
    
    if imports_ok and db_creation_ok:
        logger.info("\n🎉 All tests passed! Fixes are working.")
        return 0
    else:
        logger.info(f"\n⚠️  Some tests failed. Review the issues above.")
        return 1

if __name__ == '__main__':
    exit(main())
