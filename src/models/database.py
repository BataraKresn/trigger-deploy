"""
PostgreSQL Database Models and Configuration - Synchronous Version
Thread-safe implementation for Flask/Gunicorn multi-worker environment
"""

import os
import logging
import threading
import time
from typing import List, Dict, Optional, Any, Generator
from datetime import datetime, timezone
import json
import hashlib
import secrets
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Import sync PostgreSQL adapter instead of async
try:
    import psycopg2
    from psycopg2 import pool, sql
    from psycopg2.extras import RealDictCursor
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    SYNC_MODE = True
except ImportError:
    SYNC_MODE = False
    # Fallback to async if psycopg2 not available
    import asyncio
    import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User model for PostgreSQL"""
    id: Optional[str] = None
    nama_lengkap: str = ""
    username: str = ""
    email: str = ""
    password_hash: str = ""
    salt: str = ""
    role: str = "user"  # superadmin, user
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class ContactMessage:
    """Contact message model for PostgreSQL"""
    id: Optional[str] = None
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    company: str = ""
    subject: str = ""
    message: str = ""
    is_read: bool = False
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary excluding sensitive fields"""
        data = asdict(self)
        # Remove sensitive fields
        data.pop('password_hash', None)
        data.pop('salt', None)
        # Convert datetime to ISO format
        for field in ['created_at', 'updated_at', 'last_login']:
            if data.get(field):
                data[field] = data[field].isoformat()
        return data

    def to_safe_dict(self) -> Dict[str, Any]:
        """Convert to safe dictionary for API responses"""
        return self.to_dict()


class PostgreSQLManager:
    """PostgreSQL database manager with thread-safe connection pooling"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure one pool per application"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PostgreSQLManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, database_url: str = None, config: dict = None):
        """Initialize PostgreSQL manager"""
        if hasattr(self, '_initialized_instance'):
            return
            
        from .config import config as app_config
        
        # Validate app_config is available
        if not app_config:
            raise Exception("Application config is not available")
        
        # Build connection parameters
        if database_url:
            self.database_url = database_url
        elif config and all(k in config for k in ['user', 'password', 'host', 'port', 'database']):
            self.database_url = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        else:
            self.database_url = app_config.database_url
        
        # Validate database_url is available
        if not self.database_url:
            raise Exception("Database URL is not configured")
        
        logger.info(f"Using database URL: {self.database_url.replace(self.database_url.split('@')[0].split('//')[1], '***:***')}")
        
        # Parse URL for connection parameters
        try:
            self._parse_database_url()
        except Exception as e:
            logger.error(f"Failed to parse database URL: {e}")
            logger.error(f"Database URL format should be: postgresql://user:password@host:port/database")
            raise
        
        # Pool settings with validation
        try:
            self.min_connections = config.get('min_size', app_config.POSTGRES_MIN_CONNECTIONS) if config else app_config.POSTGRES_MIN_CONNECTIONS
            self.max_connections = config.get('max_size', app_config.POSTGRES_MAX_CONNECTIONS) if config else app_config.POSTGRES_MAX_CONNECTIONS
        except AttributeError as e:
            logger.error(f"Failed to get pool configuration: {e}")
            logger.error("Using default pool settings")
            self.min_connections = 1
            self.max_connections = 20
        
        self.pool = None
        self._initialized = False
        self._initialized_instance = True
        
        logger.info(f"PostgreSQL Manager initialized for {self.host}:{self.port}/{self.database}")
        logger.info(f"Pool settings: min={self.min_connections}, max={self.max_connections}")
    
    def _parse_database_url(self):
        """Parse database URL into components"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(self.database_url)
            
            # Validate URL format
            if not parsed.scheme or parsed.scheme != 'postgresql':
                raise ValueError(f"Invalid database URL scheme: {parsed.scheme}. Expected 'postgresql'")
            
            self.host = parsed.hostname
            self.port = parsed.port
            self.database = parsed.path.lstrip('/') if parsed.path else None
            self.user = parsed.username
            self.password = parsed.password
            
            # Validate required components
            missing_components = []
            if not self.host:
                missing_components.append('hostname')
            if not self.port:
                missing_components.append('port')
            if not self.database:
                missing_components.append('database')
            if not self.user:
                missing_components.append('username')
            if not self.password:
                missing_components.append('password')
            
            if missing_components:
                raise ValueError(f"Missing required database URL components: {', '.join(missing_components)}")
            
            # Set defaults if missing
            if not self.host:
                self.host = 'localhost'
            if not self.port:
                self.port = 5432
            if not self.database:
                self.database = 'trigger_deploy'
            if not self.user:
                self.user = 'trigger_deploy_user'
            if not self.password:
                self.password = 'secure_password_123'
                
            logger.info(f"Parsed database components: host={self.host}, port={self.port}, database={self.database}, user={self.user}")
            
        except Exception as e:
            logger.error(f"Error parsing database URL: {e}")
            logger.error(f"URL format: {self.database_url}")
            raise ValueError(f"Failed to parse database URL: {e}")
    
    def initialize(self):
        """Initialize connection pool (sync version)"""
        with self._lock:
            if self._initialized and self.pool:
                logger.info("PostgreSQL connection pool already initialized")
                return
            
            logger.info(f"Initializing PostgreSQL connection to {self.host}:{self.port}/{self.database}")
            
            # Check connectivity first
            if not self._check_connectivity():
                raise Exception(f"Cannot reach PostgreSQL server at {self.host}:{self.port}")
            
            try:
                if SYNC_MODE:
                    # Get SSL configuration
                    from .config import config as app_config
                    try:
                        ssl_config = app_config.get_postgres_ssl_config()
                    except Exception as ssl_error:
                        logger.warning(f"Failed to get SSL config: {ssl_error}")
                        ssl_config = {'sslmode': 'disable'}
                    
                    # Build connection parameters
                    conn_params = {
                        'host': self.host,
                        'port': self.port,
                        'database': self.database,
                        'user': self.user,
                        'password': self.password,
                        'cursor_factory': RealDictCursor,
                        'connect_timeout': 10,
                        'application_name': 'trigger_deploy_app'
                    }
                    
                    # Validate all required parameters are present
                    missing_params = []
                    for param in ['host', 'port', 'database', 'user', 'password']:
                        if not conn_params.get(param):
                            missing_params.append(param)
                    
                    if missing_params:
                        raise ValueError(f"Missing required connection parameters: {', '.join(missing_params)}")
                    
                    # Add SSL parameters if configured
                    try:
                        conn_params.update(ssl_config)
                    except Exception as ssl_update_error:
                        logger.warning(f"Failed to update SSL config: {ssl_update_error}")
                        conn_params['sslmode'] = 'disable'
                    
                    # Validate pool sizes
                    if self.max_connections > 100:
                        logger.warning(f"Max connections ({self.max_connections}) is very high, reducing to 50")
                        self.max_connections = 50
                    
                    if self.min_connections > self.max_connections:
                        logger.warning(f"Min connections ({self.min_connections}) > max ({self.max_connections}), adjusting")
                        self.min_connections = 1
                    
                    # Use psycopg2 connection pool
                    logger.info(f"Creating connection pool (min={self.min_connections}, max={self.max_connections})")
                    logger.info(f"SSL Mode: {ssl_config.get('sslmode', 'default')}")
                    logger.info(f"Connection timeout: {conn_params.get('connect_timeout', 10)}s")
                    
                    # Log connection parameters (safely)
                    safe_params = {k: v for k, v in conn_params.items() if k != 'password'}
                    logger.info(f"Connection parameters: {safe_params}")
                    
                    try:
                        # Validate that all connection parameters are properly set
                        for param_name, param_value in conn_params.items():
                            if param_value is None:
                                raise ValueError(f"Connection parameter '{param_name}' is None")
                            if param_name in ['host', 'database', 'user', 'password'] and not str(param_value).strip():
                                raise ValueError(f"Connection parameter '{param_name}' is empty")
                        
                        # Ensure port is integer
                        if not isinstance(conn_params['port'], int):
                            try:
                                conn_params['port'] = int(conn_params['port'])
                            except (ValueError, TypeError) as port_error:
                                raise ValueError(f"Invalid port value: {conn_params['port']} - {port_error}")
                        
                        # Create the pool with explicit error handling
                        logger.info(f"Creating ThreadedConnectionPool with minconn={self.min_connections}, maxconn={self.max_connections}")
                        
                        self.pool = psycopg2.pool.ThreadedConnectionPool(
                            minconn=self.min_connections,
                            maxconn=self.max_connections,
                            **conn_params
                        )
                        
                        if not self.pool:
                            raise Exception("ThreadedConnectionPool returned None")
                            
                    except Exception as pool_error:
                        logger.error(f"Pool creation failed: {pool_error}")
                        logger.error(f"Error type: {type(pool_error).__name__}")
                        
                        # Log the specific error details
                        if hasattr(pool_error, 'args') and pool_error.args:
                            logger.error(f"Error args: {pool_error.args}")
                        
                        # Check if it's a KeyError and log details
                        if isinstance(pool_error, KeyError):
                            logger.error(f"KeyError details: Missing key '{pool_error}' in connection parameters")
                            logger.error(f"Available connection parameters: {list(conn_params.keys())}")
                        
                        safe_params = {k: v for k, v in conn_params.items() if k != 'password'}
                        logger.error(f"Connection params (excluding password): {safe_params}")
                        raise
                    
                    # Test connection
                    logger.info("Testing database connection...")
                    conn = None
                    try:
                        conn = self.pool.getconn()
                        if not conn:
                            raise Exception("Failed to get connection from pool")
                            
                        cursor = conn.cursor()
                        cursor.execute('SELECT version()')
                        result = cursor.fetchone()
                        
                        if not result or len(result) == 0:
                            raise Exception("Empty result from version query")
                            
                        version = result[0] if result and len(result) > 0 else "Unknown"
                        logger.info(f"Connected to: {version}")
                        cursor.close()
                        logger.info("PostgreSQL connection pool created and validated successfully")
                    except Exception as test_error:
                        logger.error(f"Connection test failed: {test_error}")
                        raise
                    finally:
                        if conn:
                            try:
                                self.pool.putconn(conn)
                            except Exception as putconn_error:
                                logger.error(f"Error returning connection to pool: {putconn_error}")
                
                else:
                    # Fallback to async mode with SSL support
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        # Build asyncpg connection string with SSL
                        conn_string = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
                        
                        self.pool = loop.run_until_complete(asyncpg.create_pool(
                            conn_string,
                            min_size=self.min_connections,
                            max_size=self.max_connections,
                            command_timeout=30
                        ))
                        logger.info("PostgreSQL async connection pool created successfully")
                    finally:
                        loop.close()
                
                # Create tables and default data
                logger.info("Creating database tables...")
                self._create_tables()
                logger.info("Creating default admin user...")
                self._create_default_admin()
                
                self._initialized = True
                logger.info("PostgreSQL database manager initialization completed successfully")
                
            except psycopg2.OperationalError as e:
                error_msg = str(e).lower()
                logger.error(f"PostgreSQL OperationalError: {e}")
                
                # Check for fatal errors that shouldn't retry
                if any(fatal in error_msg for fatal in [
                    'authentication failed', 'password authentication failed',
                    'database does not exist', 'role does not exist',
                    'connection refused', 'could not connect to server'
                ]):
                    logger.error("❌ FATAL ERROR: Connection failed due to authentication/configuration issue")
                    logger.error("This is likely a configuration problem, not a temporary network issue")
                    logger.error(f"Database: {self.database}, User: {self.user}, Host: {self.host}:{self.port}")
                else:
                    logger.error(f"Network/temporary error connecting to PostgreSQL at {self.host}:{self.port}")
                
                logger.error("Verify credentials, network connectivity, and firewall settings")
                self.pool = None
                raise
            except psycopg2.Error as e:
                logger.error(f"PostgreSQL Error: {e}")
                self.pool = None
                raise
            except Exception as e:
                logger.error(f"Unexpected error initializing PostgreSQL connection pool: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                
                # Try to provide more specific error information
                if isinstance(e, KeyError):
                    logger.error(f"KeyError - Missing key: {str(e)}")
                    logger.error("This usually indicates missing environment variables or configuration")
                    
                    # List current environment variables for debugging
                    postgres_env_vars = {k: v for k, v in os.environ.items() if k.startswith('POSTGRES_')}
                    logger.error(f"Available POSTGRES_* environment variables: {list(postgres_env_vars.keys())}")
                    
                    # Check specific variables that might be missing
                    required_vars = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
                    missing_vars = [var for var in required_vars if not os.getenv(var)]
                    if missing_vars:
                        logger.error(f"Missing environment variables: {missing_vars}")
                
                elif isinstance(e, AttributeError):
                    logger.error(f"AttributeError - Missing attribute: {str(e)}")
                    logger.error("This usually indicates a problem with the config object")
                
                # Log current configuration state
                try:
                    logger.error(f"Current database URL: {self.database_url.replace(self.database_url.split('@')[0].split('//')[1], '***:***') if hasattr(self, 'database_url') else 'Not set'}")
                    logger.error(f"Parsed host: {getattr(self, 'host', 'Not set')}")
                    logger.error(f"Parsed port: {getattr(self, 'port', 'Not set')}")
                    logger.error(f"Parsed database: {getattr(self, 'database', 'Not set')}")
                    logger.error(f"Parsed user: {getattr(self, 'user', 'Not set')}")
                except Exception as log_error:
                    logger.error(f"Failed to log configuration state: {log_error}")
                
                self.pool = None
                raise

    def _check_connectivity(self) -> bool:
        """Check if PostgreSQL server is reachable"""
        import socket
        
        logger.info(f"Checking connectivity to {self.host}:{self.port}...")
        
        try:
            # Try to establish TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                logger.info(f"✅ Successfully connected to {self.host}:{self.port}")
                return True
            else:
                logger.error(f"❌ Cannot connect to {self.host}:{self.port} (error code: {result})")
                return False
                
        except socket.gaierror as e:
            logger.error(f"❌ DNS resolution failed for {self.host}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Connectivity check failed: {e}")
            return False
    
    @contextmanager
    def get_connection(self) -> Generator:
        """Get database connection from pool with context manager"""
        if not self._initialized or not self.pool:
            try:
                self.initialize()
            except Exception as init_error:
                logger.error(f"Failed to initialize database on connection request: {init_error}")
                raise
        
        if SYNC_MODE:
            conn = None
            try:
                conn = self.pool.getconn()
                if not conn:
                    raise Exception("Failed to get connection from pool - pool returned None")
                if conn.closed:
                    logger.warning("Got closed connection from pool, requesting new one")
                    self.pool.putconn(conn, close=True)
                    conn = self.pool.getconn()
                    if not conn:
                        raise Exception("Failed to get replacement connection from pool")
                yield conn
            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except Exception as rollback_error:
                        logger.warning(f"Failed to rollback connection: {rollback_error}")
                logger.error(f"Database connection error: {e}")
                raise
            finally:
                if conn:
                    try:
                        self.pool.putconn(conn)
                    except Exception as putconn_error:
                        logger.error(f"Failed to return connection to pool: {putconn_error}")
        else:
            # Fallback to async mode
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                conn = loop.run_until_complete(self.pool.acquire())
                yield conn
                loop.run_until_complete(self.pool.release(conn))
            finally:
                loop.close()
    
    @contextmanager
    def get_cursor(self, commit: bool = True) -> Generator:
        """Get database cursor with automatic transaction handling"""
        with self.get_connection() as conn:
            cursor = None
            try:
                if SYNC_MODE:
                    cursor = conn.cursor()
                    yield cursor
                    if commit:
                        conn.commit()
                else:
                    # For async fallback, return connection directly
                    yield conn
            except Exception as e:
                if SYNC_MODE:
                    conn.rollback()
                logger.error(f"Database cursor error: {e}")
                raise
            finally:
                if cursor and SYNC_MODE:
                    cursor.close()
    
    def close(self):
        """Close connection pool"""
        with self._lock:
            if self.pool:
                try:
                    if SYNC_MODE:
                        self.pool.closeall()
                    else:
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(self.pool.close())
                        finally:
                            loop.close()
                    
                    self.pool = None
                    self._initialized = False
                    logger.info("PostgreSQL connection pool closed")
                except Exception as e:
                    logger.error(f"Error closing connection pool: {e}")
    
    def health_check(self) -> bool:
        """Check database connection health with comprehensive testing"""
        try:
            if SYNC_MODE:
                with self.get_cursor(commit=False) as cursor:
                    # Test basic query
                    cursor.execute('SELECT 1 as test')
                    result = cursor.fetchone()
                    
                    if not result or len(result) == 0:
                        logger.error("Health check: Empty result from test query")
                        return False
                        
                    test_value = result[0] if result and len(result) > 0 else None
                    if test_value != 1:
                        logger.error(f"Health check: Unexpected test value: {test_value}")
                        return False
                    
                    # Test database metadata for external connection verification
                    cursor.execute("""
                        SELECT current_database(), current_user, version(), 
                               inet_server_addr(), inet_server_port()
                    """)
                    info = cursor.fetchone()
                    
                    if not info or len(info) < 3:
                        logger.error("Health check: Incomplete metadata result")
                        return False
                    
                    logger.info(f"Database health check passed:")
                    logger.info(f"  Database: {info[0] if len(info) > 0 else 'Unknown'}")
                    logger.info(f"  User: {info[1] if len(info) > 1 else 'Unknown'}")
                    logger.info(f"  Server: {info[2][:50] if len(info) > 2 and info[2] else 'Unknown'}...")
                    logger.info(f"  Server IP: {info[3] if len(info) > 3 and info[3] else 'N/A'}")
                    logger.info(f"  Server Port: {info[4] if len(info) > 4 and info[4] else 'N/A'}")
                    
                    return True
            else:
                with self.get_connection() as conn:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(conn.fetchval('SELECT 1'))
                        return result == 1
                    finally:
                        loop.close()
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            logger.warning(f"Error type: {type(e).__name__}")
            return False

    def _create_tables(self):
        """Create database tables"""
        try:
            if SYNC_MODE:
                with self.get_cursor() as cursor:
                    # Check if tables already exist
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name IN ('users', 'contact_messages', 'deployment_history')
                    """)
                    
                    result = cursor.fetchone()
                    if not result or len(result) == 0:
                        logger.warning("Could not check existing tables, proceeding with creation")
                        table_count = 0
                    else:
                        table_count = result[0] if result and len(result) > 0 else 0
                    
                    if table_count >= 3:
                        logger.info("Database tables already exist, skipping creation")
                        return
                    
                    # Create contact_messages table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS contact_messages (
                            id SERIAL PRIMARY KEY,
                            first_name VARCHAR(100) NOT NULL,
                            last_name VARCHAR(100) NOT NULL,
                            email VARCHAR(255) NOT NULL,
                            company VARCHAR(255),
                            subject VARCHAR(500) NOT NULL,
                            message TEXT NOT NULL,
                            is_read BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            read_at TIMESTAMP WITH TIME ZONE,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create users table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            nama_lengkap VARCHAR(255) NOT NULL,
                            username VARCHAR(100) UNIQUE NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            salt VARCHAR(255) NOT NULL,
                            role VARCHAR(50) DEFAULT 'user',
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP WITH TIME ZONE
                        )
                    """)
                    
                    # Create deployment_history table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS deployment_history (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            user_id UUID REFERENCES users(id),
                            action VARCHAR(100) NOT NULL,
                            target VARCHAR(255) NOT NULL,
                            status VARCHAR(50) NOT NULL,
                            details JSONB,
                            duration_seconds FLOAT,
                            ip_address INET
                        )
                    """)
                    
                    # Create indexes
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contact_messages_created_at ON contact_messages(created_at)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_deployment_history_timestamp ON deployment_history(timestamp)")
                    
                    logger.info("Database tables created successfully")
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._create_tables_async())
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def _create_default_admin(self):
        """Create default admin user if not exists"""
        try:
            if SYNC_MODE:
                with self.get_cursor() as cursor:
                    # Check if admin user already exists
                    cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", ('admin',))
                    result = cursor.fetchone()
                    
                    if not result or len(result) == 0:
                        logger.warning("Could not check existing admin user, proceeding with creation")
                        admin_exists = False
                    else:
                        admin_exists = (result[0] if result and len(result) > 0 else 0) > 0
                    
                    if not admin_exists:
                        # Create default admin user
                        password = 'admin123'
                        salt = secrets.token_hex(16)
                        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                                          password.encode('utf-8'), 
                                                          salt.encode('utf-8'), 
                                                          100000).hex()
                        
                        cursor.execute("""
                            INSERT INTO users (nama_lengkap, username, email, password_hash, salt, role)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, ('Administrator', 'admin', 'admin@trigger-deploy.local', password_hash, salt, 'admin'))
                        
                        logger.info("Default admin user created (username: admin, password: admin123)")
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._create_default_admin_async())
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Failed to create default admin user: {e}")

    # User management methods (sync versions)
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        try:
            if SYNC_MODE:
                with self.get_cursor(commit=False) as cursor:
                    cursor.execute(
                        "SELECT * FROM users WHERE username = %s AND is_active = TRUE",
                        (username,)
                    )
                    
                    user_row = cursor.fetchone()
                    if not user_row:
                        return None
                    
                    # Verify password
                    stored_hash = user_row['password_hash']
                    salt = user_row['salt']
                    password_hash = hashlib.pbkdf2_hmac('sha256', 
                                                      password.encode('utf-8'), 
                                                      salt.encode('utf-8'), 
                                                      100000).hex()
                    
                    if password_hash != stored_hash:
                        return None
                    
                    return User(
                        id=str(user_row['id']),
                        nama_lengkap=user_row['nama_lengkap'],
                        username=user_row['username'],
                        email=user_row['email'],
                        role=user_row['role'],
                        is_active=user_row['is_active'],
                        created_at=user_row['created_at'],
                        last_login=user_row['last_login']
                    )
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._authenticate_user_async(username, password))
                finally:
                    loop.close()
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            if SYNC_MODE:
                with self.get_cursor(commit=False) as cursor:
                    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                    user_row = cursor.fetchone()
                    
                    if not user_row:
                        return None
                    
                    return User(
                        id=str(user_row['id']),
                        nama_lengkap=user_row['nama_lengkap'],
                        username=user_row['username'],
                        email=user_row['email'],
                        role=user_row['role'],
                        is_active=user_row['is_active'],
                        created_at=user_row['created_at'],
                        last_login=user_row['last_login']
                    )
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._get_user_by_username_async(username))
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            if SYNC_MODE:
                with self.get_cursor(commit=False) as cursor:
                    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                    user_row = cursor.fetchone()
                    
                    if not user_row:
                        return None
                    
                    return User(
                        id=str(user_row['id']),
                        nama_lengkap=user_row['nama_lengkap'],
                        username=user_row['username'],
                        email=user_row['email'],
                        role=user_row['role'],
                        is_active=user_row['is_active'],
                        created_at=user_row['created_at'],
                        last_login=user_row['last_login']
                    )
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._get_user_by_id_async(user_id))
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        try:
            if SYNC_MODE:
                with self.get_cursor() as cursor:
                    cursor.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                        (user_id,)
                    )
                    return cursor.rowcount > 0
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._update_last_login_async(user_id))
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
            return False

    def list_users(self) -> List[User]:
        """List all users"""
        try:
            if SYNC_MODE:
                with self.get_cursor(commit=False) as cursor:
                    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
                    user_rows = cursor.fetchall()
                    
                    users = []
                    for row in user_rows:
                        users.append(User(
                            id=str(row['id']),
                            nama_lengkap=row['nama_lengkap'],
                            username=row['username'],
                            email=row['email'],
                            role=row['role'],
                            is_active=row['is_active'],
                            created_at=row['created_at'],
                            last_login=row['last_login']
                        ))
                    
                    return users
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._list_users_async())
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            if SYNC_MODE:
                with self.get_cursor(commit=False) as cursor:
                    cursor.execute("SELECT COUNT(*) FROM users")
                    total_users = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
                    active_users = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
                    admin_users = cursor.fetchone()[0]
                    
                    return {
                        'total_users': total_users or 0,
                        'active_users': active_users or 0,
                        'admin_users': admin_users or 0,
                        'inactive_users': (total_users or 0) - (active_users or 0)
                    }
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._get_user_stats_async())
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}

    def create_user(self, user_data: Dict[str, Any]) -> Optional[User]:
        """Create a new user"""
        try:
            if SYNC_MODE:
                with self.get_cursor() as cursor:
                    # Check if username or email already exists
                    cursor.execute(
                        "SELECT COUNT(*) FROM users WHERE username = %s OR email = %s",
                        (user_data['username'], user_data['email'])
                    )
                    
                    if cursor.fetchone()[0] > 0:
                        logger.warning(f"User with username {user_data['username']} or email {user_data['email']} already exists")
                        return None
                    
                    # Hash password
                    password = user_data.get('password', 'temppassword123')
                    salt = secrets.token_hex(16)
                    password_hash = hashlib.pbkdf2_hmac('sha256', 
                                                      password.encode('utf-8'), 
                                                      salt.encode('utf-8'), 
                                                      100000).hex()
                    
                    # Insert user
                    cursor.execute("""
                        INSERT INTO users (nama_lengkap, username, email, password_hash, salt, role, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        user_data['nama_lengkap'],
                        user_data['username'],
                        user_data['email'],
                        password_hash,
                        salt,
                        user_data.get('role', 'user'),
                        user_data.get('is_active', True)
                    ))
                    
                    user_id = cursor.fetchone()[0]
                    return self.get_user_by_id(str(user_id))
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._create_user_async(user_data))
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[User]:
        """Update user data"""
        try:
            if SYNC_MODE:
                with self.get_cursor() as cursor:
                    # Build update query dynamically
                    updates = []
                    params = []
                    
                    for field in ['nama_lengkap', 'username', 'email', 'role', 'is_active']:
                        if field in user_data:
                            updates.append(f"{field} = %s")
                            params.append(user_data[field])
                    
                    if not updates:
                        return self.get_user_by_id(user_id)
                    
                    query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
                    params.append(user_id)
                    
                    cursor.execute(query, params)
                    
                    if cursor.rowcount > 0:
                        return self.get_user_by_id(user_id)
                    return None
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._update_user_async(user_id, user_data))
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return None

    def update_user_password(self, user_id: str, new_password: str) -> bool:
        """Update user password"""
        try:
            if SYNC_MODE:
                with self.get_cursor() as cursor:
                    # Hash new password
                    salt = secrets.token_hex(16)
                    password_hash = hashlib.pbkdf2_hmac('sha256', 
                                                      new_password.encode('utf-8'), 
                                                      salt.encode('utf-8'), 
                                                      100000).hex()
                    
                    cursor.execute(
                        "UPDATE users SET password_hash = %s, salt = %s WHERE id = %s",
                        (password_hash, salt, user_id)
                    )
                    
                    return cursor.rowcount > 0
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._update_user_password_async(user_id, new_password))
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Error updating user password: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete by marking as inactive)"""
        try:
            if SYNC_MODE:
                with self.get_cursor() as cursor:
                    cursor.execute(
                        "UPDATE users SET is_active = FALSE WHERE id = %s",
                        (user_id,)
                    )
                    
                    return cursor.rowcount > 0
            else:
                # Async fallback
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self._delete_user_async(user_id))
                finally:
                    loop.close()
                
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False


class ContactMessageManager:
    """Contact Message management operations"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db_manager = db_manager
    
    async def create_message(self, message_data: dict) -> bool:
        """Create a new contact message"""
        try:
            conn = await self.db_manager.get_connection()
            if not conn:
                return False
            
            await conn.execute('''
                INSERT INTO contact_messages (first_name, last_name, email, company, subject, message)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', 
                message_data['first_name'],
                message_data['last_name'], 
                message_data['email'],
                message_data.get('company', ''),
                message_data['subject'],
                message_data['message']
            )
            
            logger.info(f"Contact message created from {message_data['email']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create contact message: {e}")
            return False
    
    async def get_all_messages(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """Get all contact messages with pagination"""
        try:
            conn = await self.db_manager.get_connection()
            if not conn:
                return []
            
            rows = await conn.fetch('''
                SELECT id, first_name, last_name, email, company, subject, message, 
                       is_read, created_at, read_at
                FROM contact_messages 
                ORDER BY created_at DESC 
                LIMIT $1 OFFSET $2
            ''', limit, offset)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get contact messages: {e}")
            return []
    
    async def get_unread_count(self) -> int:
        """Get count of unread messages"""
        try:
            conn = await self.db_manager.get_connection()
            if not conn:
                return 0
            
            count = await conn.fetchval('SELECT COUNT(*) FROM contact_messages WHERE is_read = FALSE')
            return count or 0
            
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
            return 0
    
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read"""
        try:
            conn = await self.db_manager.get_connection()
            if not conn:
                return False
            
            await conn.execute('''
                UPDATE contact_messages 
                SET is_read = TRUE, read_at = CURRENT_TIMESTAMP 
                WHERE id = $1
            ''', message_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")
            return False
    
    async def delete_message(self, message_id: str) -> bool:
        """Delete a contact message"""
        try:
            conn = await self.db_manager.get_connection()
            if not conn:
                return False
            
            await conn.execute('DELETE FROM contact_messages WHERE id = $1', message_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            return False


# Global database manager instance
db_manager = None
contact_manager = None
_init_lock = threading.Lock()


def get_db_manager() -> Optional[PostgreSQLManager]:
    """Get database manager instance (thread-safe singleton)"""
    global db_manager
    
    if db_manager is None:
        with _init_lock:
            if db_manager is None:
                try:
                    logger.info("Initializing PostgreSQL database manager...")
                    
                    # Pre-validate configuration before creating manager
                    from .config import config as app_config
                    
                    # Check if required configuration is available
                    if not hasattr(app_config, 'DATABASE_URL') or not app_config.DATABASE_URL:
                        logger.error("DATABASE_URL is not configured")
                        return None
                    
                    # Check environment variables that might be missing
                    required_env_vars = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
                    missing_env_vars = []
                    for var in required_env_vars:
                        if not os.getenv(var):
                            missing_env_vars.append(var)
                    
                    if missing_env_vars:
                        logger.warning(f"Missing environment variables: {missing_env_vars}")
                        logger.warning("Will use default values from configuration")
                    
                    # Create database manager
                    db_manager = PostgreSQLManager()
                    
                    # Initialize the manager
                    db_manager.initialize()
                    logger.info("Database manager initialized successfully")
                    
                except KeyError as ke:
                    logger.error(f"KeyError during database initialization: {ke}")
                    logger.error("This usually indicates missing environment variables or configuration keys")
                    logger.error("Check that all required PostgreSQL environment variables are set")
                    
                    # List available environment variables for debugging
                    postgres_env_vars = {k: v for k, v in os.environ.items() if k.startswith('POSTGRES_')}
                    logger.error(f"Available POSTGRES_* environment variables: {list(postgres_env_vars.keys())}")
                    return None
                    
                except Exception as e:
                    logger.error(f"Failed to initialize database manager: {e}")
                    logger.error(f"Error type: {type(e).__name__}")
                    logger.error("Database features will be unavailable")
                    logger.error("Application will fall back to file-based user management")
                    
                    # Additional debugging info
                    try:
                        from .config import config as app_config
                        logger.error(f"Config DATABASE_URL available: {bool(getattr(app_config, 'DATABASE_URL', None))}")
                        logger.error(f"Config POSTGRES_HOST: {getattr(app_config, 'POSTGRES_HOST', 'Not set')}")
                        logger.error(f"Config POSTGRES_PORT: {getattr(app_config, 'POSTGRES_PORT', 'Not set')}")
                    except Exception as config_error:
                        logger.error(f"Could not access config for debugging: {config_error}")
                    
                    return None
    
    # Verify pool is still healthy
    if db_manager and not db_manager.pool:
        logger.warning("Database manager exists but pool is None")
        logger.warning("This indicates the database connection pool failed to initialize")
        return None
    
    return db_manager


def init_database():
    """Initialize database (sync version)"""
    return get_db_manager() is not None


def close_database():
    """Close database connections"""
    global db_manager
    if db_manager:
        db_manager.close()
        db_manager = None


def get_contact_manager() -> Optional[ContactMessageManager]:
    """Get contact manager instance"""
    global contact_manager
    
    if contact_manager is None:
        db = get_db_manager()
        if db:
            contact_manager = ContactMessageManager(db)
    
    return contact_manager
