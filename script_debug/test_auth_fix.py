#!/usr/bin/env python3
"""
Test script for authentication fixes
"""

import asyncio
import sys
import os
import logging

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.database import init_database, get_db_manager, close_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection and authentication"""
    try:
        logger.info("Testing database initialization...")
        db = await init_database()
        
        if not db:
            logger.error("Failed to initialize database")
            return False
        
        logger.info("Testing database health check...")
        is_healthy = await db.health_check()
        logger.info(f"Database health: {'OK' if is_healthy else 'FAILED'}")
        
        if not is_healthy:
            logger.info("Attempting reconnection...")
            await db.reconnect()
            is_healthy = await db.health_check()
            logger.info(f"Database health after reconnect: {'OK' if is_healthy else 'FAILED'}")
        
        # Test authentication with default admin
        logger.info("Testing authentication...")
        from src.models.config import config
        
        user = await db.authenticate_user(
            config.DEFAULT_ADMIN_USERNAME,
            config.DEFAULT_ADMIN_PASSWORD
        )
        
        if user:
            logger.info(f"Authentication successful for user: {user.username}")
        else:
            logger.error("Authentication failed")
            return False
        
        # Test user stats
        logger.info("Testing user statistics...")
        stats = await db.get_user_stats()
        logger.info(f"User stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    finally:
        try:
            await close_database()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")

def main():
    """Run the test"""
    try:
        result = asyncio.run(test_database_connection())
        if result:
            logger.info("✅ All tests passed!")
            sys.exit(0)
        else:
            logger.error("❌ Tests failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
