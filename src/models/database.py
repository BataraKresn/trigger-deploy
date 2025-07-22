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


def check_table_exists(table_name: str) -> bool:
    """
    Check if a specific table exists in the database.
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Use information_schema to check table existence
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                )
            """), {'table_name': table_name})
            return result.scalar()
    except Exception as e:
        logger.warning(f"Error checking if table '{table_name}' exists: {e}")
        return False


def check_schema_exists() -> bool:
    """
    Check if the main application tables exist in the database.
    
    Returns:
        bool: True if schema exists, False otherwise
    """
    try:
        # Check for key tables that should exist
        key_tables = ['users']  # Add other critical tables here
        
        for table_name in key_tables:
            if not check_table_exists(table_name):
                logger.debug(f"Table '{table_name}' does not exist")
                return False
        
        logger.debug("All key tables exist in the database")
        return True
        
    except Exception as e:
        logger.warning(f"Error checking schema existence: {e}")
        return False


def init_db() -> bool:
    """
    Initialize database schema by creating all tables.
    This operation is idempotent and safe for existing databases.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        engine = get_engine()
        
        # Check if schema already exists and is complete
        if check_schema_exists() and validate_database_integrity():
            logger.info("Database schema already exists and is complete, skipping table creation")
            # Still fix sequences if needed
            fix_sequence_issues()
            return True
        
        logger.info("Creating or repairing database schema...")
        
        # Import all models to ensure they are registered with Base
        from .user import User
        
        # Create all tables defined in models (safe operation with checkfirst=True)
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        # Fix any sequence issues after table creation
        fix_sequence_issues()
        
        # Validate that everything was created correctly
        if not validate_database_integrity():
            logger.warning("Database schema creation completed but integrity check failed, attempting recovery...")
            if not safe_database_recovery():
                logger.error("Database schema initialization and recovery both failed")
                return False
        
        logger.info("Database schema initialization completed successfully")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Database schema initialization failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during schema initialization: {e}")
        return False


def validate_database_integrity() -> bool:
    """
    Validate that the database schema is complete and consistent.
    
    Returns:
        bool: True if database is in good state, False otherwise
    """
    try:
        engine = get_engine()
        
        with engine.connect() as conn:
            # Check if users table exists and has expected structure
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            if not columns:
                logger.warning("Users table does not exist or has no columns")
                return False
            
            # Check for required columns
            column_names = [col[0] for col in columns]
            required_columns = ['id', 'username', 'email', 'password_hash', 'role']
            
            missing_columns = [col for col in required_columns if col not in column_names]
            if missing_columns:
                logger.warning(f"Users table missing required columns: {missing_columns}")
                return False
            
            logger.debug(f"Database integrity check passed - found {len(columns)} columns in users table")
            return True
            
    except Exception as e:
        logger.warning(f"Database integrity check failed: {e}")
        return False


def fix_sequence_issues():
    """
    Fix sequence issues that might occur when tables already exist.
    This helps resolve duplicate key violations on sequences.
    """
    try:
        engine = get_engine()
        
        with engine.connect() as conn:
            # Check if users table exists
            if not check_table_exists('users'):
                logger.debug("Users table doesn't exist, skipping sequence fix")
                return True
            
            # Fix users table sequence
            logger.info("Checking and fixing database sequences...")
            
            # Get the current maximum ID from users table
            result = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM users"))
            max_id = result.scalar()
            
            # Reset the sequence to be higher than the current max ID
            if max_id > 0:
                new_seq_value = max_id + 1
                conn.execute(text(f"SELECT setval('users_id_seq', {new_seq_value}, false)"))
                logger.info(f"Reset users_id_seq to {new_seq_value}")
            
            conn.commit()
            return True
            
    except Exception as e:
        logger.warning(f"Could not fix sequence issues: {e}")
        return False


def safe_database_recovery() -> bool:
    """
    Attempt to recover from partial database initialization.
    This is called when integrity checks fail.
    
    Returns:
        bool: True if recovery successful, False otherwise
    """
    try:
        logger.info("Attempting database recovery...")
        
        # Try to create missing tables only
        engine = get_engine()
        
        # Import User model to ensure it's registered
        from .user import User
        
        # Create only missing tables
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        # Re-validate integrity
        if validate_database_integrity():
            logger.info("Database recovery successful")
            return True
        else:
            logger.error("Database recovery failed - integrity check still failing")
            return False
            
    except Exception as e:
        logger.error(f"Database recovery failed: {e}")
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
    Includes idempotent schema and admin user creation.
    
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
        
        logger.info("Database connection established successfully")
        
        # Log current database status
        log_database_status()
        
        # Initialize schema (idempotent operation)
        logger.info("Checking and initializing database schema...")
        if not init_db():
            logger.error("Database schema initialization failed")
            return False
        
        logger.info("Database initialization completed successfully")
        
        # Ensure admin user exists (idempotent operation)
        logger.info("Checking and creating admin user if needed...")
        try:
            db_manager = DatabaseManager()
            if db_manager.ensure_admin_exists():
                logger.info("Admin user verification/creation completed successfully")
            else:
                logger.warning("Admin user verification/creation failed - continuing anyway")
        except Exception as e:
            logger.warning(f"Admin user verification error (non-critical): {e}")
        
        # Final status log
        log_database_status()
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def log_database_status():
    """
    Log current database status for debugging purposes.
    """
    try:
        engine = get_engine()
        
        with engine.connect() as conn:
            # Check database version
            result = conn.execute(text("SELECT version()"))
            pg_version = result.scalar()
            logger.info(f"PostgreSQL version: {pg_version}")
            
            # Check existing tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            if tables:
                logger.info(f"Existing tables: {', '.join(tables)}")
            else:
                logger.info("No tables found in database")
            
            # Check user count if users table exists
            if 'users' in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
                logger.info(f"Current user count: {user_count}")
                
                # Check admin users
                result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role IN ('admin', 'superadmin')"))
                admin_count = result.scalar()
                logger.info(f"Current admin count: {admin_count}")
            
    except Exception as e:
        logger.warning(f"Could not log database status: {e}")


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
            username: Username or email
            password: Password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            # Import here to avoid circular imports
            from .user import User
            
            # Try to find user by username or email
            user = session.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if user and user.check_password(password) and user.is_active:
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
    
    def get_user_by_email(self, email: str) -> Optional[Any]:
        """
        Get user by email.
        
        Args:
            email: Email to search for
            
        Returns:
            User object if found, None otherwise
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            from .user import User
            user = session.query(User).filter(User.email == email).first()
            return user
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
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
                      Required: username, email, password
                      Optional: full_name, role
            
        Returns:
            Created user object or None if failed
        """
        session = self.get_session()
        if not session:
            return None
        
        try:
            from .user import User
            
            # Check if username or email already exists
            existing_user = session.query(User).filter(
                (User.username == user_data.get('username')) | 
                (User.email == user_data.get('email'))
            ).first()
            
            if existing_user:
                logger.error("User with this username or email already exists")
                return None
            
            # Create new user
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data.get('full_name', ''),
                role=user_data.get('role', 'user')
            )
            
            # Set password
            user.set_password(user_data['password'])
            
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
            from datetime import datetime
            
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
    
    def create_default_admin(self) -> bool:
        """
        Create default admin user if none exists.
        Uses environment variables for default credentials.
        This function is idempotent and safe to call multiple times.
        
        Returns:
            bool: True if created or already exists, False if failed
        """
        session = self.get_session()
        if not session:
            logger.error("Failed to get database session for admin creation")
            return False
        
        try:
            from .user import User
            
            # Get admin credentials from environment
            admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
            admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
            admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@example.com')
            
            # Check if the specific admin user already exists
            existing_admin = session.query(User).filter(
                (User.username == admin_username) | (User.email == admin_email)
            ).first()
            
            if existing_admin:
                logger.info(f"Admin user already exists: {existing_admin.username} ({existing_admin.email})")
                return True
            
            # Check if any admin users exist at all
            admin_count = session.query(User).filter(
                User.role.in_(['admin', 'superadmin'])
            ).count()
            
            if admin_count > 0:
                logger.info(f"Found {admin_count} existing admin user(s), skipping default admin creation")
                return True
            
            logger.info("No admin users found, creating default admin user...")
            
            # Create default admin user
            admin_user = User(
                username=admin_username,
                email=admin_email,
                full_name='Default Administrator',
                role='superadmin'
            )
            admin_user.set_password(admin_password)
            
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            
            logger.info(f"Default admin user created successfully: {admin_username} (ID: {admin_user.id})")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create default admin user: {e}")
            return False
        finally:
            session.close()
    
    def ensure_admin_exists(self) -> bool:
        """
        Ensure at least one admin user exists in the system.
        
        Returns:
            bool: True if admin exists or was created, False otherwise
        """
        if os.getenv('AUTO_CREATE_ADMIN', 'true').lower() == 'true':
            return self.create_default_admin()
        return True
    
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
    
    def get_all_users(self) -> List[Any]:
        """
        Get list of all users (alias for list_users for API compatibility).
        
        Returns:
            List of user objects
        """
        return self.list_users()
    
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
