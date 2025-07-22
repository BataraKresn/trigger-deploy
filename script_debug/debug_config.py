#!/usr/bin/env python3
"""
Debug Configuration Script
Check environment variables and configuration for database connectivity issues
"""

import os
import sys
import logging
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check PostgreSQL environment variables"""
    logger.info("🔍 Checking Environment Variables")
    logger.info("=" * 50)
    
    # Required PostgreSQL environment variables
    postgres_vars = [
        'POSTGRES_HOST',
        'POSTGRES_PORT', 
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'DATABASE_URL'
    ]
    
    # Optional but important variables
    optional_vars = [
        'POSTGRES_SSL_MODE',
        'POSTGRES_MIN_CONNECTIONS',
        'POSTGRES_MAX_CONNECTIONS',
        'DEPLOY_TOKEN'
    ]
    
    missing_required = []
    
    logger.info("Required Variables:")
    for var in postgres_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var or 'TOKEN' in var:
                logger.info(f"  ✅ {var}: ****** (set)")
            else:
                logger.info(f"  ✅ {var}: {value}")
        else:
            logger.info(f"  ❌ {var}: Not set")
            missing_required.append(var)
    
    logger.info("\nOptional Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var or 'TOKEN' in var:
                logger.info(f"  ✅ {var}: ****** (set)")
            else:
                logger.info(f"  ✅ {var}: {value}")
        else:
            logger.info(f"  ⚠️  {var}: Not set (using default)")
    
    return missing_required

def check_config_loading():
    """Check if config can be loaded properly"""
    logger.info("\n🔍 Checking Configuration Loading")
    logger.info("=" * 50)
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/models'))
        
        from config import config
        logger.info("✅ Configuration loaded successfully")
        
        # Check important config values
        logger.info(f"  DATABASE_URL: {'***@***' if config.DATABASE_URL else 'Not set'}")
        logger.info(f"  POSTGRES_HOST: {config.POSTGRES_HOST}")
        logger.info(f"  POSTGRES_PORT: {config.POSTGRES_PORT}")
        logger.info(f"  POSTGRES_DB: {config.POSTGRES_DB}")
        logger.info(f"  POSTGRES_USER: {config.POSTGRES_USER}")
        logger.info(f"  SSL_MODE: {config.POSTGRES_SSL_MODE}")
        logger.info(f"  MIN_CONNECTIONS: {config.POSTGRES_MIN_CONNECTIONS}")
        logger.info(f"  MAX_CONNECTIONS: {config.POSTGRES_MAX_CONNECTIONS}")
        
        # Test SSL config
        try:
            ssl_config = config.get_postgres_ssl_config()
            logger.info(f"  SSL Config: {ssl_config}")
        except Exception as e:
            logger.error(f"  ❌ SSL Config Error: {e}")
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Failed to load configuration: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return None

def validate_database_url(config=None):
    """Validate database URL format"""
    logger.info("\n🔍 Validating Database URL")
    logger.info("=" * 50)
    
    try:
        if config and hasattr(config, 'DATABASE_URL'):
            db_url = config.DATABASE_URL
        else:
            db_url = os.getenv('DATABASE_URL')
        
        if not db_url:
            logger.error("❌ DATABASE_URL is not set")
            return False
        
        # Parse URL
        parsed = urlparse(db_url)
        
        logger.info(f"Database URL Components:")
        logger.info(f"  Scheme: {parsed.scheme}")
        logger.info(f"  Hostname: {parsed.hostname}")
        logger.info(f"  Port: {parsed.port}")
        logger.info(f"  Database: {parsed.path.lstrip('/') if parsed.path else 'None'}")
        logger.info(f"  Username: {parsed.username}")
        logger.info(f"  Password: {'***' if parsed.password else 'None'}")
        
        # Validate components
        issues = []
        if parsed.scheme != 'postgresql':
            issues.append(f"Invalid scheme: {parsed.scheme} (should be 'postgresql')")
        if not parsed.hostname:
            issues.append("Missing hostname")
        if not parsed.port:
            issues.append("Missing port")
        if not parsed.path or parsed.path == '/':
            issues.append("Missing database name")
        if not parsed.username:
            issues.append("Missing username")
        if not parsed.password:
            issues.append("Missing password")
        
        if issues:
            logger.error("❌ Database URL validation failed:")
            for issue in issues:
                logger.error(f"    {issue}")
            return False
        else:
            logger.info("✅ Database URL validation passed")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error validating database URL: {e}")
        return False

def test_database_manager_creation():
    """Test creating database manager"""
    logger.info("
🔍 Testing Database Manager Creation")
    logger.info("=" * 50)
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        from models.database import PostgreSQLManager
        
        logger.info("Creating PostgreSQLManager instance...")
        
        # Test with explicit error handling for KeyError
        try:
            manager = PostgreSQLManager()
        except KeyError as ke:
            logger.error(f"KeyError during PostgreSQLManager creation: {ke}")
            logger.error("This indicates a missing configuration key or environment variable")
            
            # Check what might be missing
            postgres_env_vars = {k: v for k, v in os.environ.items() if k.startswith('POSTGRES_')}
            logger.error(f"Available POSTGRES_* environment variables: {list(postgres_env_vars.keys())}")
            
            return False
        
        logger.info("✅ PostgreSQLManager created successfully")
        logger.info(f"  Manager: {manager}")
        logger.info(f"  Host: {getattr(manager, 'host', 'Not set')}")
        logger.info(f"  Port: {getattr(manager, 'port', 'Not set')}")
        logger.info(f"  Database: {getattr(manager, 'database', 'Not set')}")
        logger.info(f"  User: {getattr(manager, 'user', 'Not set')}")
        logger.info(f"  Min Connections: {getattr(manager, 'min_connections', 'Not set')}")
        logger.info(f"  Max Connections: {getattr(manager, 'max_connections', 'Not set')}")
        
        # Test initialization separately
        logger.info("Testing manager initialization...")
        try:
            manager.initialize()
            logger.info("✅ Manager initialization successful")
            return True
        except KeyError as ke:
            logger.error(f"KeyError during initialization: {ke}")
            return False
        except Exception as init_error:
            logger.error(f"Initialization failed: {init_error}")
            logger.error(f"Error type: {type(init_error).__name__}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Failed to create PostgreSQLManager: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Import traceback for detailed error
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        
        return False

def main():
    """Main diagnostic function"""
    logger.info("🚀 Database Configuration Diagnostic")
    logger.info("=" * 60)
    
    # Check 1: Environment variables
    missing_vars = check_environment_variables()
    
    # Check 2: Configuration loading
    config = check_config_loading()
    
    # Check 3: Database URL validation
    url_valid = validate_database_url(config)
    
    # Check 4: Database manager creation
    manager_created = test_database_manager_creation()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Diagnostic Summary:")
    logger.info(f"  Environment Variables: {'✅ OK' if not missing_vars else f'❌ Missing: {missing_vars}'}")
    logger.info(f"  Configuration Loading: {'✅ OK' if config else '❌ FAILED'}")
    logger.info(f"  Database URL:          {'✅ OK' if url_valid else '❌ INVALID'}")
    logger.info(f"  Manager Creation:      {'✅ OK' if manager_created else '❌ FAILED'}")
    
    if missing_vars:
        logger.info(f"\n💡 To fix missing environment variables, run:")
        for var in missing_vars:
            if var == 'DATABASE_URL':
                logger.info(f"  export {var}='postgresql://user:password@host:port/database'")
            elif var == 'POSTGRES_HOST':
                logger.info(f"  export {var}='localhost'  # or your PostgreSQL server IP")
            elif var == 'POSTGRES_PORT':
                logger.info(f"  export {var}='5432'")
            elif var == 'POSTGRES_DB':
                logger.info(f"  export {var}='trigger_deploy'")
            elif var == 'POSTGRES_USER':
                logger.info(f"  export {var}='trigger_deploy_user'")
            elif var == 'POSTGRES_PASSWORD':
                logger.info(f"  export {var}='your_password_here'")
    
    if all([not missing_vars, config, url_valid, manager_created]):
        logger.info("\n🎉 All checks passed! Database configuration looks good.")
        return 0
    else:
        logger.info(f"\n⚠️  Some checks failed. Review the issues above.")
        return 1

if __name__ == '__main__':
    exit(main())