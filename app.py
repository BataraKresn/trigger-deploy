#!/usr/bin/env python3
# =================================
# Trigger Deploy Server - Clean Architecture with PostgreSQL
# =================================

import os
import sys
import logging
import asyncio
import atexit
import time
from flask import Flask
from flask_cors import CORS

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.config import config
from src.routes.main import main_bp
from src.routes.api import api_bp
from src.routes.deploy import deploy_bp

# Import PostgreSQL routes instead of file-based user routes
try:
    from src.routes.user_postgres import user_bp
    USING_POSTGRES = True
    logging.info("Using PostgreSQL user management")
except ImportError:
    from src.routes.user import user_bp
    USING_POSTGRES = False
    logging.warning("PostgreSQL not available, falling back to file-based user management")

# Database initialization
if USING_POSTGRES:
    from src.models.database import init_db_manager_sync, close_database


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_app():
    """Application factory"""
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Enable CORS
    CORS(app)
    
    # Configure app
    app.config['SECRET_KEY'] = config.TOKEN
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_LOG_SIZE
    
    # Initialize PostgreSQL database if available
    if USING_POSTGRES:
        retry_count = 0
        max_retries = 5
        retry_delay = 2  # seconds
        
        while retry_count < max_retries:
            try:
                # Initialize database manager synchronously
                init_db_manager_sync()
                logger.info("PostgreSQL database initialized successfully")
                
                # Register cleanup function
                def cleanup_db():
                    try:
                        # Create new loop for cleanup if needed
                        cleanup_loop = None
                        try:
                            cleanup_loop = asyncio.get_event_loop()
                            if cleanup_loop.is_closed():
                                cleanup_loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(cleanup_loop)
                        except RuntimeError:
                            cleanup_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(cleanup_loop)
                        
                        cleanup_loop.run_until_complete(close_database())
                        logger.info("PostgreSQL database connection closed")
                    except Exception as e:
                        logger.error(f"Error closing database: {e}")
                
                atexit.register(cleanup_db)
                break  # Success, exit retry loop
                
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Failed to initialize PostgreSQL database (attempt {retry_count}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to initialize PostgreSQL database after {max_retries} attempts: {e}")
                    logger.info("Falling back to file-based user management")
                    # Note: USING_POSTGRES already defined at import time
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(deploy_bp)
    app.register_blueprint(user_bp)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'timestamp': os.times()}, 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    logger.info("Application initialized successfully")
    return app


if __name__ == '__main__':
    app = create_app()
    
    # Create required directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs(config.LOG_DIR, exist_ok=True)
    
    # Setup graceful shutdown for database connections
    if USING_POSTGRES:
        def cleanup_database():
            """Cleanup database connections on shutdown"""
            try:
                import asyncio
                from src.models.database import close_database
                logger.info("Cleaning up database connections...")
                
                # Create new event loop for cleanup if needed
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(close_database())
                loop.close()
                logger.info("Database cleanup completed")
            except Exception as e:
                logger.error(f"Error during database cleanup: {e}")
        
        atexit.register(cleanup_database)
    
    logger.info("Starting Trigger Deploy Server...")
    logger.info(f"Log directory: {config.LOG_DIR}")
    logger.info(f"Servers config: {config.SERVERS_FILE}")
    logger.info(f"PostgreSQL enabled: {USING_POSTGRES}")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        if USING_POSTGRES:
            logger.info("Performing final cleanup...")
            cleanup_database()
