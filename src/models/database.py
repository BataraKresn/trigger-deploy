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
        
        # Build connection parameters
        if database_url:
            self.database_url = database_url
        elif config and all(k in config for k in ['user', 'password', 'host', 'port', 'database']):
            self.database_url = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        else:
            self.database_url = app_config.database_url
        
        # Parse URL for connection parameters
        self._parse_database_url()
        
        # Pool settings
        self.min_connections = config.get('min_size', app_config.POSTGRES_MIN_CONNECTIONS) if config else app_config.POSTGRES_MIN_CONNECTIONS
        self.max_connections = config.get('max_size', app_config.POSTGRES_MAX_CONNECTIONS) if config else app_config.POSTGRES_MAX_CONNECTIONS
        
        self.pool = None
        self._initialized = False
        self._initialized_instance = True
        
        logger.info(f"PostgreSQL Manager initialized for {self.host}:{self.port}/{self.database}")
    
    def _parse_database_url(self):
        """Parse database URL into components"""
        from urllib.parse import urlparse
        
        parsed = urlparse(self.database_url)
        self.host = parsed.hostname or 'localhost'
        self.port = parsed.port or 5432
        self.database = parsed.path.lstrip('/') if parsed.path else 'trigger_deploy'
        self.user = parsed.username or 'trigger_deploy_user'
        self.password = parsed.password or 'secure_password_123'
    
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
                    ssl_config = app_config.get_postgres_ssl_config()
                    
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
                    
                    # Add SSL parameters if configured
                    conn_params.update(ssl_config)
                    
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
                    
                    try:
                        self.pool = psycopg2.pool.ThreadedConnectionPool(
                            minconn=self.min_connections,
                            maxconn=self.max_connections,
                            **conn_params
                        )
                    except Exception as pool_error:
                        logger.error(f"Pool creation failed: {pool_error}")
                        safe_params = {k: v for k, v in conn_params.items() if k != 'password'}
                        logger.error(f"Connection params (excluding password): {safe_params}")
                        raise
                    
                    # Test connection
                    logger.info("Testing database connection...")
                    conn = self.pool.getconn()
                    try:
                        cursor = conn.cursor()
                        cursor.execute('SELECT version()')
                        version = cursor.fetchone()[0]
                        logger.info(f"Connected to: {version}")
                        cursor.close()
                        logger.info("PostgreSQL connection pool created and validated successfully")
                    finally:
                        self.pool.putconn(conn)
                
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
            self.initialize()
        
        if SYNC_MODE:
            conn = None
            try:
                conn = self.pool.getconn()
                if conn.closed:
                    self.pool.putconn(conn, close=True)
                    conn = self.pool.getconn()
                yield conn
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"Database connection error: {e}")
                raise
            finally:
                if conn:
                    self.pool.putconn(conn)
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
                    if not result or result[0] != 1:
                        return False
                    
                    # Test database metadata for external connection verification
                    cursor.execute("""
                        SELECT current_database(), current_user, version(), 
                               inet_server_addr(), inet_server_port()
                    """)
                    info = cursor.fetchone()
                    
                    logger.info(f"Database health check passed:")
                    logger.info(f"  Database: {info[0]}")
                    logger.info(f"  User: {info[1]}")
                    logger.info(f"  Server: {info[2][:50] if info[2] else 'Local'}...")
                    logger.info(f"  Server IP: {info[3] if info[3] else 'N/A'}")
                    logger.info(f"  Server Port: {info[4] if info[4] else 'N/A'}")
                    
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
                    
                    if cursor.fetchone()[0] >= 3:
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
                    
                    if cursor.fetchone()[0] == 0:
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
                    db_manager = PostgreSQLManager()
                    db_manager.initialize()
                    logger.info("Database manager initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize database manager: {e}")
                    logger.error("Database features will be unavailable")
                    return None
    
    # Verify pool is still healthy
    if db_manager and not db_manager.pool:
        logger.warning("Database manager exists but pool is None")
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
