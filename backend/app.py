"""
Professional Deploy Server Flask Application with PostgreSQL Integration
Refactored for scalability, modularity, and production readiness
"""
import os
from flask import Flask, request, jsonify
from flask_restx import Api, Resource
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from loguru import logger
from datetime import datetime, timezone
import traceback

# Import models and services
from models import init_db
from services.deploy_service import DeploymentService
from services.health_service import HealthService
from services.log_service import LogService
from services.server_service import ServerService

# Import routes
from routes import deploy_bp, health_bp, logs_bp, auth_bp, server_bp


def create_app(config_name='production'):
    """
    Application factory pattern for creating Flask app
    """
    app = Flask(__name__)
    
    # Load configuration
    configure_app(app, config_name)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup logging
    setup_logging(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        try:
            from models import db
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
    
    return app


def configure_app(app: Flask, config_name: str):
    """Configure Flask application"""
    
    # Basic Flask configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-this')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 60)) * 60
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        'postgresql+psycopg2://deployuser:strongpassword@localhost:5432/deploydb'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # API Documentation configuration
    app.config['RESTX_MASK_SWAGGER'] = False
    app.config['RESTX_VALIDATE'] = True
    
    # Rate limiting configuration
    app.config['RATELIMIT_STORAGE_URL'] = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    logger.info(f"Application configured for {config_name} environment")


def initialize_extensions(app: Flask):
    """Initialize Flask extensions"""
    
    # Database
    from models import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:3111", "http://localhost:8082"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # JWT
    jwt = JWTManager(app)
    
    # Rate Limiting
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config['RATELIMIT_STORAGE_URL']
    )
    
    # API Documentation
    api = Api(
        app,
        version='1.0',
        title=os.getenv('API_TITLE', 'Deploy Server API'),
        description=os.getenv('API_DESCRIPTION', 'Professional Deploy Server REST API with PostgreSQL integration'),
        doc='/docs/',
        prefix='/api'
    )
    
    # Store extensions in app for access in routes
    app.extensions['api'] = api
    app.extensions['limiter'] = limiter
    app.extensions['jwt'] = jwt
    
    logger.info("Flask extensions initialized successfully")


def register_blueprints(app: Flask):
    """Register application blueprints"""
    
    # Get API instance
    api = app.extensions['api']
    
    # Register namespaces with API documentation
    from routes import register_namespaces
    register_namespaces(api)
    
    # Register basic routes
    @app.route('/api/status')
    def api_status():
        """API status endpoint"""
        return jsonify({
            'status': 'success',
            'message': 'Deploy Server API is running',
            'data': {
                'version': '1.0',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'environment': os.getenv('FLASK_ENV', 'production')
            }
        })
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for load balancers"""
        try:
            # Check database connection
            from models import db
            db.session.execute('SELECT 1')
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'database': 'connected'
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }), 503
    
    @app.route('/')
    def index():
        """Root endpoint"""
        return jsonify({
            'message': 'Deploy Server API',
            'documentation': '/docs/',
            'status': '/api/status',
            'health': '/health'
        })
    
    logger.info("Application blueprints registered successfully")


def setup_logging(app: Flask):
    """Setup application logging"""
    
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure loguru
    logger.remove()  # Remove default handler
    
    # Console logging
    logger.add(
        sink=lambda x: print(x, end=''),
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # File logging
    logger.add(
        sink=log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    logger.info("Application logging configured successfully")


def setup_error_handlers(app: Flask):
    """Setup global error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'Resource not found',
            'data': None
        }), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'status': 'error',
            'message': 'Bad request',
            'data': None
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized access',
            'data': None
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'status': 'error',
            'message': 'Forbidden access',
            'data': None
        }), 403
    
    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Internal server error: {str(error)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'data': None
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {str(error)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'data': None
        }), 500
    
    logger.info("Error handlers configured successfully")


# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Development server
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5001)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )