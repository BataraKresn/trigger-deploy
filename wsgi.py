import logging
import os

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Loading wsgi.py...")

try:
    from app import app, initialize_components
    logger.info("✅ Successfully imported app and initialize_components")
except Exception as e:
    logger.error(f"❌ Failed to import from app: {e}")
    raise

# Initialize components when module is loaded
try:
    logger.info("Initializing components for Gunicorn deployment...")
    initialize_components()
    logger.info("✅ Components initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize components: {e}")
    raise

if __name__ == "__main__":
    app.run()
