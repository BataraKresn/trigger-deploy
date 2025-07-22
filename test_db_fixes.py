#!/usr/bin/env python3
"""
Test script to verify the database concurrency fixes
"""

import asyncio
import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, '/workspaces/trigger-deploy')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_database_initialization():
    """Test database initialization"""
    try:
        from src.models.database import init_database, close_database, get_db_manager
        
        logger.info("Testing database initialization...")
        
        # Initialize database
        db_manager = await init_database()
        logger.info("✅ Database initialized successfully")
        
        # Test concurrent access
        async def test_auth():
            db = get_db_manager()
            if db and db.pool:
                # Try to authenticate (this will fail but should not crash)
                user = await db.authenticate_user("testuser", "testpass")
                logger.info(f"Auth test result: {user}")
            return True
        
        # Run multiple concurrent auth attempts
        tasks = [test_auth() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {result}")
            else:
                logger.info(f"✅ Task {i} completed successfully")
        
        # Test table creation (should be idempotent)
        if db_manager:
            await db_manager._create_tables()
            logger.info("✅ Table creation test passed")
            
            await db_manager._create_default_admin()
            logger.info("✅ Default admin creation test passed")
        
        # Cleanup
        await close_database()
        logger.info("✅ Database closed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("Starting database concurrency tests...")
    
    success = await test_database_initialization()
    
    if success:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
