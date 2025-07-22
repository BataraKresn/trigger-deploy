"""
Database module for Trigger Deploy Server
Provides SQLAlchemy configuration and helper functions for PostgreSQL integration.
"""

import os
import logging
from typing import Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

# Configure logging
logger = logging.getLogger(__name__)

# Global SQLAlchemy objects
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None
Base = declarative_base()

def get_database_url() -> str:
    """
    Construct PostgreSQL database URL from environment variables.
    
    Returns:
        str: Complete PostgreSQL connection URL
        
    Raises:
        ValueError: If required environment variables are missing
    """
    # Load configuration from environment variables
    host = os.getenv('POSTGRES_HOST')
    port = os.getenv('POSTGRES_PORT', '5432')
    database = os.getenv('POSTGRES_DB')
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    ssl_mode = os.getenv('POSTGRES_SSL_MODE', 'disable')
    
    # Validate required parameters
    required_vars = {
        'POSTGRES_HOST': host,
        'POSTGRES_DB': database,
        'POSTGRES_USER': user,
        'POSTGRES_PASSWORD': password
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # URL-encode password to handle special characters
    encoded_password = quote_plus(password)
    
    # Construct connection URL
    database_url = f"postgresql://{user}:{encoded_password}@{host}:{port}/{database}"
    
    # Add SSL mode parameter
    database_url += f"?sslmode={ssl_mode}"
    
    logger.debug(f"Database URL constructed for host: {host}:{port}, database: {database}")
    return database_url


def create_database_engine() -> Engine:
    """
    Create SQLAlchemy engine with connection pooling.
    
    Returns:
        Engine: Configured SQLAlchemy engine
        
    Raises:
        SQLAlchemyError: If engine creation fails
    """
    database_url = get_database_url()
    
    # Get connection pool settings
    max_connections = int(os.getenv('POSTGRES_MAX_CONNECTIONS', '10'))
    connection_timeout = int(os.getenv('POSTGRES_CONNECTION_TIMEOUT', '10'))
    
    try:
        # Create engine with connection pooling
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=max_connections // 2,  # Base pool size
            max_overflow=max_connections // 2,  # Overflow connections
            pool_timeout=connection_timeout,
            pool_recycle=3600,  # Recycle connections every hour
            pool_pre_ping=True,  # Validate connections before use
            echo=False,  # Set to True for SQL query logging in development
            future=True  # Use SQLAlchemy 2.0 style
        )
        
        logger.info(f"Database engine created successfully with pool size: {max_connections}")
        return engine
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database engine: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating database engine: {e}")
        raise SQLAlchemyError(f"Engine creation failed: {e}")


def get_engine() -> Engine:
    """
    Get the global SQLAlchemy engine instance.
    
    Returns:
        Engine: The global SQLAlchemy engine
        
    Raises:
        RuntimeError: If engine is not initialized
    """
    global engine
    if engine is None:
        raise RuntimeError("Database engine not initialized. Call init_database() first.")
    return engine


def get_session() -> Session:
    """
    Create a new database session.
    
    Returns:
        Session: New SQLAlchemy session instance
        
    Raises:
        RuntimeError: If SessionLocal is not initialized
    """
    global SessionLocal
    if SessionLocal is None:
        raise RuntimeError("Database session factory not initialized. Call init_database() first.")
    return SessionLocal()


def init_db() -> bool:
    """
    Initialize database schema by creating all tables.
    This operation is safe and won't overwrite existing tables.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = get_engine()
        
        # Create all tables defined in models (safe operation)
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database schema initialization completed successfully")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database schema initialization failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during schema initialization: {e}")
        return False


def test_database_connection() -> bool:
    """
    Test database connectivity by executing a simple query.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        
        # Test connection with a simple query
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()
            
        logger.info("Database connection test successful")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database connection test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during connection test: {e}")
        return False


def init_database() -> bool:
    """
    Initialize the database module and establish connections.
    This function should be called once during application startup.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    global engine, SessionLocal
    
    try:
        logger.info("Initializing database connection...")
        
        # Create engine
        engine = create_database_engine()
        
        # Create session factory
        SessionLocal = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        # Test the connection
        if not test_database_connection():
            logger.error("Database connection test failed during initialization")
            return False
        
        # Initialize schema
        if not init_db():
            logger.error("Database schema initialization failed")
            return False
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def close_database() -> None:
    """
    Clean up database connections and resources.
    This function should be called during application shutdown.
    """
    global engine, SessionLocal
    
    try:
        if engine:
            engine.dispose()
            logger.info("Database engine disposed successfully")
        
        engine = None
        SessionLocal = None
        
    except Exception as e:
        logger.error(f"Error during database cleanup: {e}")


def get_db_session():
    """
    Context manager for database sessions.
    Useful for dependency injection in Flask routes.
    
    Yields:
        Session: Database session that will be automatically closed
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


# Database manager class for backward compatibility
class DatabaseManager:
    """
    Database manager class providing high-level database operations.
    Maintains backward compatibility with existing code.
    """
    
    @staticmethod
    def get_engine() -> Engine:
        """Get the database engine."""
        return get_engine()
    
    @staticmethod
    def get_session() -> Session:
        """Get a new database session."""
        return get_session()
    
    @staticmethod
    def test_connection() -> bool:
        """Test database connectivity."""
        return test_database_connection()
    
    @staticmethod
    def initialize() -> bool:
        """Initialize the database."""
        return init_database()
    
    @staticmethod
    def close() -> None:
        """Close database connections."""
        close_database()


# Global database manager instance for backward compatibility
db_manager = DatabaseManager()

# Export commonly used objects
__all__ = [
    'Base',
    'engine',
    'SessionLocal',
    'get_engine',
    'get_session',
    'init_db',
    'init_database',
    'close_database',
    'get_db_session',
    'db_manager',
    'DatabaseManager'
]
