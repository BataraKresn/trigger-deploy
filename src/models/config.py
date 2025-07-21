# =================================
# Configuration Models
# =================================

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration"""
    
    # Security
    TOKEN: str = os.getenv("DEPLOY_TOKEN")  # For deployment operations
    LOGIN_PASSWORD: str = os.getenv("LOGIN_PASSWORD", "admin")  # For web login authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET")  # For JWT token signing
    
    # PostgreSQL Database Configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "trigger_deploy")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "trigger_deploy_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Database Pool Settings
    POSTGRES_MIN_CONNECTIONS: int = int(os.getenv("POSTGRES_MIN_CONNECTIONS", "1"))
    POSTGRES_MAX_CONNECTIONS: int = int(os.getenv("POSTGRES_MAX_CONNECTIONS", "20"))
    POSTGRES_CONNECTION_TIMEOUT: int = int(os.getenv("POSTGRES_CONNECTION_TIMEOUT", "10"))
    POSTGRES_COMMAND_TIMEOUT: int = int(os.getenv("POSTGRES_COMMAND_TIMEOUT", "5"))
    
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
    SERVERS_FILE: str = os.getenv("SERVERS_FILE", "config/servers.json")
    SERVICES_FILE: str = os.getenv("SERVICES_FILE", "config/services.json")
    
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
        
        # Build DATABASE_URL if not provided
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        # Create log directory if it doesn't exist
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)

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
