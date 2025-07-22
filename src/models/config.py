# =================================
# Configuration Models
# =================================

import os
from dataclasses import dataclass

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass


@dataclass
class Config:
    """Application configuration"""
    
    # Security
    TOKEN: str = os.getenv("DEPLOY_TOKEN")  # For deployment operations
    LOGIN_PASSWORD: str = os.getenv("LOGIN_PASSWORD", "admin")  # For web login authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET")  # For JWT token signing
    
    # PostgreSQL Database Configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432")) if os.getenv("POSTGRES_PORT", "").isdigit() else 5432
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "trigger_deploy")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "trigger_deploy_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # SSL/Security Settings for External Database
    POSTGRES_SSL_MODE: str = os.getenv("POSTGRES_SSL_MODE", "prefer")  # disable, allow, prefer, require, verify-ca, verify-full
    POSTGRES_SSL_CERT_PATH: str = os.getenv("POSTGRES_SSL_CERT_PATH", "")
    POSTGRES_SSL_KEY_PATH: str = os.getenv("POSTGRES_SSL_KEY_PATH", "")
    POSTGRES_SSL_CA_PATH: str = os.getenv("POSTGRES_SSL_CA_PATH", "")
    
    # Connection Health Check Settings
    POSTGRES_HEALTH_CHECK_ENABLED: bool = os.getenv("POSTGRES_HEALTH_CHECK_ENABLED", "true").lower() == "true"
    POSTGRES_HEALTH_CHECK_INTERVAL: int = int(os.getenv("POSTGRES_HEALTH_CHECK_INTERVAL", "120"))  # seconds - reduced from 30 to 120
    
    # Database Pool Settings
    POSTGRES_MIN_CONNECTIONS: int = int(os.getenv("POSTGRES_MIN_CONNECTIONS", "1")) if os.getenv("POSTGRES_MIN_CONNECTIONS", "").isdigit() else 1
    POSTGRES_MAX_CONNECTIONS: int = int(os.getenv("POSTGRES_MAX_CONNECTIONS", "20")) if os.getenv("POSTGRES_MAX_CONNECTIONS", "").isdigit() else 20
    POSTGRES_CONNECTION_TIMEOUT: int = int(os.getenv("POSTGRES_CONNECTION_TIMEOUT", "10")) if os.getenv("POSTGRES_CONNECTION_TIMEOUT", "").isdigit() else 10
    POSTGRES_COMMAND_TIMEOUT: int = int(os.getenv("POSTGRES_COMMAND_TIMEOUT", "5")) if os.getenv("POSTGRES_COMMAND_TIMEOUT", "").isdigit() else 5
    
    # Authentication Settings
    POSTGRES_AUTH_ENABLED: bool = os.getenv("POSTGRES_AUTH_ENABLED", "true").lower() == "true"
    AUTO_CREATE_ADMIN: bool = os.getenv("AUTO_CREATE_ADMIN", "true").lower() == "true"
    DEFAULT_ADMIN_USERNAME: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@trigger-deploy.local")
    
    # Logging
    LOG_DIR: str = os.getenv("LOG_DIR", "trigger-logs")
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", "7"))
    MAX_LOG_SIZE: int = int(os.getenv("MAX_LOG_SIZE", "10485760"))
    
    # Server Configuration  
    SERVERS_FILE: str = os.getenv("SERVERS_FILE", "static/servers.json")
    SERVICES_FILE: str = os.getenv("SERVICES_FILE", "static/services.json")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Email Notifications
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
    EMAIL_TO: str = os.getenv("EMAIL_TO", "")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # Docker
    DOCKER_ENABLED: bool = os.getenv("DOCKER_ENABLED", "True").lower() == "true"
    
    # Demo Credentials Display
    SHOW_DEMO_CREDENTIALS: bool = os.getenv("SHOW_DEMO_CREDENTIALS", "False").lower() == "true"
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.TOKEN:
            raise ValueError("DEPLOY_TOKEN environment variable is required")
        
        # Set JWT secret if not provided - use deploy token as fallback
        if not self.JWT_SECRET:
            self.JWT_SECRET = self.TOKEN + "_jwt_secret"
        
        # Validate PostgreSQL configuration
        self._validate_postgres_config()
        
        # Auto-detect environment and adjust database host
        self._adjust_database_host()
        
        # Build DATABASE_URL if not provided
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        # Create log directory if it doesn't exist
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)

    def _validate_postgres_config(self):
        """Validate PostgreSQL configuration"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Check for missing required PostgreSQL environment variables
        required_postgres_vars = {
            'POSTGRES_HOST': self.POSTGRES_HOST,
            'POSTGRES_PORT': self.POSTGRES_PORT,
            'POSTGRES_DB': self.POSTGRES_DB,
            'POSTGRES_USER': self.POSTGRES_USER,
            'POSTGRES_PASSWORD': self.POSTGRES_PASSWORD
        }
        
        missing_vars = []
        for var_name, var_value in required_postgres_vars.items():
            # Check if the value is the default value (indicating env var not set)
            env_value = os.getenv(var_name)
            if not env_value:
                if var_name == 'POSTGRES_HOST' and var_value != 'localhost':
                    continue  # Host auto-detection handled elsewhere
                missing_vars.append(var_name)
        
        if missing_vars:
            logger.warning(f"Missing PostgreSQL environment variables: {missing_vars}")
            logger.warning("Using default values. For production, set these environment variables:")
            for var in missing_vars:
                default_value = required_postgres_vars[var.replace('POSTGRES_', '').lower()]
                if 'PASSWORD' in var:
                    logger.warning(f"  {var}=<your_password>")
                else:
                    logger.warning(f"  {var}={default_value}")
        
        # Validate pool settings
        if self.POSTGRES_MIN_CONNECTIONS < 1:
            logger.warning(f"POSTGRES_MIN_CONNECTIONS ({self.POSTGRES_MIN_CONNECTIONS}) must be >= 1, setting to 1")
            self.POSTGRES_MIN_CONNECTIONS = 1
        
        if self.POSTGRES_MAX_CONNECTIONS < self.POSTGRES_MIN_CONNECTIONS:
            logger.warning(f"POSTGRES_MAX_CONNECTIONS ({self.POSTGRES_MAX_CONNECTIONS}) < min ({self.POSTGRES_MIN_CONNECTIONS}), adjusting")
            self.POSTGRES_MAX_CONNECTIONS = max(self.POSTGRES_MIN_CONNECTIONS, 20)
        
        logger.info(f"PostgreSQL configuration validated:")
        logger.info(f"  Host: {self.POSTGRES_HOST}")
        logger.info(f"  Port: {self.POSTGRES_PORT}")
        logger.info(f"  Database: {self.POSTGRES_DB}")
        logger.info(f"  User: {self.POSTGRES_USER}")
        logger.info(f"  Pool: {self.POSTGRES_MIN_CONNECTIONS}-{self.POSTGRES_MAX_CONNECTIONS} connections")
        logger.info(f"  SSL Mode: {self.POSTGRES_SSL_MODE}")

    def _adjust_database_host(self):
        """Auto-detect environment and adjust PostgreSQL host"""
        import socket
        
        # Skip auto-adjustment if using external IP
        if self.POSTGRES_HOST not in ['postgres', 'localhost', '127.0.0.1']:
            print(f"Using external PostgreSQL server: {self.POSTGRES_HOST}:{self.POSTGRES_PORT}")
            return
        
        # Auto-detection logic for local/docker environments
        # If we're running in Docker container, use 'postgres' hostname
        # If we're running on host, use 'localhost'
        
        # Check if we can reach postgres hostname (Docker internal)
        try:
            socket.getaddrinfo('postgres', self.POSTGRES_PORT)
            # We can reach 'postgres' hostname - we're in Docker network
            if self.POSTGRES_HOST == 'postgres':
                pass  # Keep as is
            elif self.DATABASE_URL and 'postgres:' in self.DATABASE_URL:
                pass  # Keep as is
        except socket.gaierror:
            # Cannot reach 'postgres' hostname - we're on host
            if self.POSTGRES_HOST == 'postgres':
                print("Detected host environment, adjusting PostgreSQL host from 'postgres' to 'localhost'")
                self.POSTGRES_HOST = 'localhost'
            
            # Also update DATABASE_URL if it uses postgres hostname
            if self.DATABASE_URL and '@postgres:' in self.DATABASE_URL:
                print("Updating DATABASE_URL to use localhost instead of postgres")
                self.DATABASE_URL = self.DATABASE_URL.replace('@postgres:', '@localhost:')

    def get_postgres_ssl_config(self) -> dict:
        """Get PostgreSQL SSL configuration"""
        ssl_config = {}
        
        try:
            # Always set sslmode, even if disabled
            ssl_mode = self.POSTGRES_SSL_MODE or 'disable'
            ssl_config['sslmode'] = ssl_mode
            
            # Only add SSL cert/key if SSL is enabled and paths are provided
            if ssl_mode not in ['disable', 'allow']:
                if self.POSTGRES_SSL_CERT_PATH and os.path.exists(self.POSTGRES_SSL_CERT_PATH):
                    ssl_config['sslcert'] = self.POSTGRES_SSL_CERT_PATH
                
                if self.POSTGRES_SSL_KEY_PATH and os.path.exists(self.POSTGRES_SSL_KEY_PATH):
                    ssl_config['sslkey'] = self.POSTGRES_SSL_KEY_PATH
                    
                if self.POSTGRES_SSL_CA_PATH and os.path.exists(self.POSTGRES_SSL_CA_PATH):
                    ssl_config['sslrootcert'] = self.POSTGRES_SSL_CA_PATH
            
            return ssl_config
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error building SSL config: {e}")
            # Return safe default
            return {'sslmode': 'disable'}
        
        return ssl_config

    @property
    def database_url(self) -> str:
        """Get database URL with proper fallback"""
        return self.DATABASE_URL

    def get_postgres_config(self) -> dict:
        """Get PostgreSQL configuration as dictionary"""
        return {
            'host': self.POSTGRES_HOST,
            'port': self.POSTGRES_PORT,
            'database': self.POSTGRES_DB,
            'user': self.POSTGRES_USER,
            'password': self.POSTGRES_PASSWORD,
            'min_size': self.POSTGRES_MIN_CONNECTIONS,
            'max_size': self.POSTGRES_MAX_CONNECTIONS,
            'command_timeout': self.POSTGRES_COMMAND_TIMEOUT
        }


# Global config instance
config = Config()


def get_config() -> Config:
    """Get global config instance"""
    return config
