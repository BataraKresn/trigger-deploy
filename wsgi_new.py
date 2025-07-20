#!/usr/bin/env python3
# =================================
# WSGI Entry Point for Production
# =================================

import logging
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Loading WSGI application...")

try:
    from app import create_app
    app = create_app()
    logger.info("✅ Successfully created Flask application")
except Exception as e:
    logger.error(f"❌ Failed to create app: {e}")
    raise

if __name__ == "__main__":
    app.run()
