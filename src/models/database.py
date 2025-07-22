"""
Database module for Trigger Deploy Server
Provides SQLAlchemy configuration and database manager for PostgreSQL integration.
"""

import os
import logging
from typing import Optional, Dict, List, Any
from urllib.parse import quote_plus
from datetime import datetime

from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.pool import QueuePool

# Configure logging
logger = logging.getLogger(__name__)

# Global SQLAlchemy objects
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None
Base = declarative_base()

# Global database manager instance
_db_manager_instance = None


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
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            
        logger.debug("Database connection test successful")
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
    global engine, SessionLocal, _db_manager_instance
    
    try:
        if engine:
            engine.dispose()
            logger.info("Database engine disposed successfully")
        
        engine = None
        SessionLocal = None
        _db_manager_instance = None
        
    except Exception as e:
        logger.error(f"Error during database cleanup: {e}")


class DatabaseManager:
    """
    Database manager class providing high-level database operations.
    Maintains backward compatibility with existing code.
    """
    
    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._initialized = False
        self._pool = None
    
    @property
    def pool(self):
        """
        Expose the connection pool for backward compatibility.
        Returns the SQLAlchemy engine's pool or None if not initialized.
        """
        if not self._ensure_initialized():
            return None
        
        if self._engine and hasattr(self._engine, 'pool'):
            return self._engine.pool
        
        return self._pool
    
    @property
    def engine(self):
        """
        Expose the SQLAlchemy engine.
        """
        if not self._ensure_initialized():
            return None
        return self._engine
    
    def _ensure_initialized(self) -> bool:
        """Ensure the database manager is initialized."""
        if not self._initialized:
            try:
                self._engine = get_engine()
                self._session_factory = SessionLocal
                # Set pool reference for backward compatibility
                if self._engine and hasattr(self._engine, 'pool'):
                    self._pool = self._engine.pool
                self._initialized = True
                logger.debug("Database manager initialized successfully")
                return True
            except Exception as e:
                logger.warning(f"Database manager initialization failed: {e}")
                return False
        return True
    
    def get_connection(self):
        """
        Get a raw database connection from the pool.
        Provides compatibility with legacy connection pool usage.
        """
        if not self._ensure_initialized():
            return None
        
        try:
            # Get raw connection from SQLAlchemy engine
            connection = self._engine.raw_connection()
            return connection
        except Exception as e:
            logger.error(f"Failed to get raw connection: {e}")
            return None
    
    def return_connection(self, connection):
        """
        Return a connection to the pool.
        Provides compatibility with legacy connection pool usage.
        """
        if connection:
            try:
                connection.close()
            except Exception as e:
                logger.error(f"Failed to return connection: {e}")
    
    def close_all_connections(self):
        """
        Close all connections in the pool.
        Provides compatibility with legacy connection pool usage.
        """
        if self._engine:
            try:
                self._engine.dispose()
                logger.info("All database connections closed")
            except Exception as e:
                logger.error(f"Failed to close all connections: {e}")
    
    def get_pool_status(self) -> Dict:
        """
        Get connection pool status information.
        """
        if not self._ensure_initialized() or not self.pool:
            return {
                'status': 'unavailable',
                'size': 0,
                'checked_in': 0,
                'checked_out': 0,
                'overflow': 0
            }
        
        try:
            pool = self.pool
            return {
                'status': 'available',
                'size': getattr(pool, 'size', lambda: 0)(),
                'checked_in': getattr(pool, 'checkedin', lambda: 0)(),
                'checked_out': getattr(pool, 'checkedout', lambda: 0)(),
                'overflow': getattr(pool, 'overflow', lambda: 0)(),
                'invalid': getattr(pool, 'invalidated', lambda: 0)()
            }
        except Exception as e:
            logger.error(f"Failed to get pool status: {e}")
    def create_all_tables(self) -> bool:
        """
        Create all database tables defined in models.
        Safe operation that won't overwrite existing tables.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return init_db()
    
    def drop_all_tables(self) -> bool:
        """
        Drop all database tables. Use with caution!
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self._ensure_initialized():
            return False
        
        try:
            Base.metadata.drop_all(bind=self._engine)
            logger.warning("All database tables dropped")
            return True
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            return False
    
    def health_check(self) -> bool:
        """
        Check database health and connectivity.
        
        Returns:
            bool: True if database is healthy, False otherwise
        """
        if not self._ensure_initialized():
            return False
        
        return test_database_connection()
    
    def get_session(self) -> Optional[Session]:
        """
        Get a new database session.
        
        Returns:
            Session: New database session or None if not available
        """
        if not self._ensure_initialized():
            return None
        
        try:
            return get_session()
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None
    
    def execute_query(self, query: str, params: Dict = None) -> Optional[List[Dict]]:
        """
        Execute a raw SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries representing query results or None if failed
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            result = session.execute(text(query), params or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            else:
                session.commit()
                return []
        except Exception as e:
            session.rollback()
            logger.error(f"Query execution failed: {e}")
            return None
        finally:
            session.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Any]:
        """
        Authenticate user credentials.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # This is a placeholder - implement based on your User model
        session = self.get_session()
        if not session:
            return None
        
        try:
            # Import here to avoid circular imports
            from .user import User
            user = session.query(User).filter(User.username == username).first()
            if user and user.check_password(password):
                return user
            return None
        except Exception as e:
            logger.error(f"User authentication failed: {e}")
            return None
        finally:
            session.close()
    
    def get_user_by_username(self, username: str) -> Optional[Any]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User object if found, None otherwise
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            from .user import User
            user = session.query(User).filter(User.username == username).first()
            return user
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}")
            return None
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[Any]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User object if found, None otherwise
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            from .user import User
            user = session.query(User).filter(User.id == user_id).first()
            return user
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
        finally:
            session.close()
    
    def create_user(self, user_data: Dict) -> Optional[Any]:
        """
        Create a new user.
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Created user object or None if failed
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            from .user import User
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create user: {e}")
            return None
        finally:
            session.close()
    
    def update_last_login(self, user_id: int) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        session = self.get_session()
        if not session:
            return False
        
        try:
            from .user import User
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update last login: {e}")
            return False
        finally:
            session.close()
    
    def list_users(self) -> List[Any]:
        """
        Get list of all users.
        
        Returns:
            List of user objects
        """
        session = self.get_session()
        if not session:
            return []
        
        try:
            from .user import User
            users = session.query(User).all()
            return users
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []
        finally:
            session.close()
    
    def get_user_stats(self) -> Dict:
        """
        Get user statistics.
        
        Returns:
            Dictionary containing user statistics
        """
        session = self.get_session()
        if not session:
            return {}
        
        try:
            from .user import User
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            admin_users = session.query(User).filter(User.is_admin == True).count()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'admin_users': admin_users,
                'inactive_users': total_users - active_users
            }
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {}
        finally:
            session.close()
    
    def log_audit(self, user_id: int, action: str, resource: str, 
                  ip_address: str = None, user_agent: str = None) -> bool:
        """
        Log audit event.
        
        Args:
            user_id: User ID performing the action
            action: Action performed
            resource: Resource affected
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            bool: True if successful, False otherwise
        """
        session = self.get_session()
        if not session:
            return False
        
        try:
            # Create audit log entry
            audit_data = {
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'timestamp': datetime.utcnow()
            }
            
            # You can implement AuditLog model later
            # For now, we'll just log it
            logger.info(f"Audit log: {audit_data}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False
        finally:
            session.close()


def get_db_manager() -> Optional[DatabaseManager]:
    """
    Get the global database manager instance.
    This function provides backward compatibility with existing code.
    
    Returns:
        DatabaseManager: Global database manager instance or None if not available
    """
    global _db_manager_instance
    
    # Check if required environment variables exist
    required_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables for database: {', '.join(missing_vars)}")
        return None
    
    # Check if database is initialized
    if engine is None or SessionLocal is None:
        logger.warning("Database not initialized, attempting to initialize...")
        try:
            if not init_database():
                logger.error("Failed to initialize database for db_manager")
                return None
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            return None
    
    # Create manager instance if not exists
    if _db_manager_instance is None:
        try:
            _db_manager_instance = DatabaseManager()
            
            # Verify the manager is working
            if _db_manager_instance.pool is None:
                logger.error("Database manager created but pool is not available")
                _db_manager_instance = None
                return None
            
            logger.debug("Database manager instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create database manager instance: {e}")
            _db_manager_instance = None
            return None
    
    return _db_manager_instance


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
    'get_db_manager',
    'DatabaseManager'
]
