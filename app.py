#!/usr/bin/env python3
# =================================
# Trigger Deploy Server - Clean Architecture
# =================================

import os
import sys
import logging
from flask import Flask
from flask_cors import CORS

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.config import config
from src.routes.main import main_bp
from src.routes.api import api_bp
from src.routes.deploy import deploy_bp


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
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(deploy_bp)
    
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
    
    logger.info("Starting Trigger Deploy Server...")
    logger.info(f"Log directory: {config.LOG_DIR}")
    logger.info(f"Servers config: {config.SERVERS_FILE}")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
