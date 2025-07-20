# =================================
# Configuration Models
# =================================

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration"""
    
    # Security
    TOKEN: str = os.getenv("DEPLOY_TOKEN")
    
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
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.TOKEN:
            raise ValueError("DEPLOY_TOKEN environment variable is required")
        
        # Create log directory if it doesn't exist
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)


# Global config instance
config = Config()
