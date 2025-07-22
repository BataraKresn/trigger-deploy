"""
PostgreSQL Database Models and Configuration
"""

import os
import asyncio
import asyncpg
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import json
import hashlib
import secrets
from dataclasses import dataclass, asdict
import logging

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
    """PostgreSQL database manager with connection pooling"""
    
    def __init__(self, database_url: str = None, config: dict = None):
        """Initialize PostgreSQL manager
        
        Args:
            database_url: Direct database URL string
            config: Database configuration dictionary with connection settings
        """
        from .config import config as app_config
        
        # Set database URL from parameter or config
        if database_url:
            self.database_url = database_url
        elif config and all(k in config for k in ['user', 'password', 'host', 'port', 'database']):
            self.database_url = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        else:
            # Fallback to environment variables or app config
            self.database_url = app_config.database_url
            
        # Connection pool settings
        self.min_connections = config.get('min_size', app_config.POSTGRES_MIN_CONNECTIONS) if config else app_config.POSTGRES_MIN_CONNECTIONS
        self.max_connections = config.get('max_size', app_config.POSTGRES_MAX_CONNECTIONS) if config else app_config.POSTGRES_MAX_CONNECTIONS
        self.command_timeout = config.get('command_timeout', app_config.POSTGRES_COMMAND_TIMEOUT) if config else app_config.POSTGRES_COMMAND_TIMEOUT
        
        self.pool = None
        self._initialization_lock = asyncio.Lock()
        self._initialized = False
        
        # Security: Log connection info without password
        safe_url = self.database_url.split('@')[0].split(':')[:-1]
        safe_url = ':'.join(safe_url) + ':***@[REDACTED]'
        logger.info(f"PostgreSQL Manager initialized with URL: {safe_url}")

    async def initialize(self):
        """Initialize connection pool"""
        async with self._initialization_lock:
            if self._initialized and self.pool:
                logger.info("PostgreSQL connection pool already initialized")
                return
                
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=self.min_connections,
                    max_size=self.max_connections,
                    command_timeout=self.command_timeout,
                    server_settings={
                        'application_name': 'trigger_deploy_app',
                        'timezone': 'UTC'
                    }
                )
                logger.info("PostgreSQL connection pool created successfully")
                
                # Validate pool with a simple query
                async with self.pool.acquire() as conn:
                    await conn.fetchval('SELECT 1')
                logger.info("PostgreSQL connection pool validated successfully")
                
                # Create tables and default data
                await self._create_tables()
                await self._create_default_admin()
                
                self._initialized = True
                
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL pool: {e}")
                if self.pool:
                    await self.pool.close()
                    self.pool = None
                self._initialized = False
                raise

    async def close(self):
        """Close connection pool gracefully"""
        if self.pool:
            try:
                # Close all connections gracefully
                await self.pool.close()
                self.pool = None
                self._initialized = False
                logger.info("PostgreSQL connection pool closed gracefully")
            except Exception as e:
                logger.error(f"Error closing PostgreSQL pool: {e}")
                self.pool = None
                self._initialized = False

    async def health_check(self):
        """Check database connection health"""
        if not self.pool or not self._initialized:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            return True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    async def reconnect(self):
        """Reconnect to database if connection is lost"""
        logger.info("Attempting to reconnect to database...")
        await self.close()
        await self.initialize()
        logger.info("Database reconnection completed")

    async def _create_tables(self):
        """Create database tables"""
        conn = None
        try:
            conn = await self.pool.acquire()
            
            # Check if tables already exist to avoid concurrent creation
            tables_exist = await conn.fetchval('''
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN ('users', 'deployment_history', 'audit_logs')
            ''')
            
            if tables_exist >= 3:
                logger.info("Database tables already exist, skipping creation")
                return
            
            # Use transaction to ensure atomicity
            async with conn.transaction():
                # Create update_updated_at function for triggers
                await conn.execute('''
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                ''')
                
                # Users table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        nama_lengkap VARCHAR(255) NOT NULL DEFAULT '',
                        username VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        salt VARCHAR(255) NOT NULL,
                        role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('superadmin', 'user')),
                        is_active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP WITH TIME ZONE NULL
                    )
                ''')
                
                # Create updated_at trigger for users table
                await conn.execute('''
                    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
                    CREATE TRIGGER update_users_updated_at 
                        BEFORE UPDATE ON users 
                        FOR EACH ROW 
                        EXECUTE FUNCTION update_updated_at_column();
                ''')
                
                # Deployment history table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS deployment_history (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        server_name VARCHAR(255) NOT NULL,
                        service_name VARCHAR(255) NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        trigger_type VARCHAR(50) DEFAULT 'manual',
                        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                        username VARCHAR(100) NOT NULL,
                        start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP WITH TIME ZONE NULL,
                        duration_seconds INTEGER DEFAULT 0,
                        logs TEXT DEFAULT '',
                        error_message TEXT DEFAULT '',
                        metadata JSONB DEFAULT '{}'::jsonb,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Audit logs table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                        action VARCHAR(100) NOT NULL,
                        resource VARCHAR(255) NOT NULL,
                        details JSONB DEFAULT '{}'::jsonb,
                        ip_address INET,
                        user_agent TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Indexes for performance - with individual error handling
                indexes = [
                    ('idx_users_username', 'users(username)'),
                    ('idx_users_email', 'users(email)'),
                    ('idx_users_active', 'users(is_active)'),
                    ('idx_deployment_history_server', 'deployment_history(server_name)'),
                    ('idx_deployment_history_user', 'deployment_history(user_id)'),
                    ('idx_deployment_history_created', 'deployment_history(created_at)'),
                    ('idx_audit_logs_user', 'audit_logs(user_id)'),
                    ('idx_audit_logs_action', 'audit_logs(action)'),
                    ('idx_audit_logs_created', 'audit_logs(created_at)')
                ]
                
                for idx_name, idx_columns in indexes:
                    try:
                        await conn.execute(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_columns}')
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.debug(f"Index {idx_name} already exists, skipping")
                        else:
                            logger.warning(f"Failed to create index {idx_name}: {e}")
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            if "already exists" in str(e).lower() or "tuple concurrently updated" in str(e).lower():
                logger.info("Database tables already exist or being created by another process, skipping")
            else:
                logger.error(f"Failed to create tables: {e}")
                # Don't raise the exception to prevent initialization failure
        finally:
            if conn:
                await self.pool.release(conn)

    async def _create_default_admin(self):
        """Create default admin user if not exists"""
        conn = None
        try:
            from .config import config as app_config
            
            if not app_config.AUTO_CREATE_ADMIN:
                logger.info("Auto-create admin is disabled")
                return
                
            conn = await self.pool.acquire()
            
            # Check if admin user exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM users WHERE username = $1 OR email = $2",
                app_config.DEFAULT_ADMIN_USERNAME,
                app_config.DEFAULT_ADMIN_EMAIL
            )
            
            if existing_user:
                logger.info(f"Admin user '{app_config.DEFAULT_ADMIN_USERNAME}' already exists, skipping creation")
                return
            
            # Create admin user
            salt = secrets.token_hex(32)
            password_hash = self._hash_password(app_config.DEFAULT_ADMIN_PASSWORD, salt)
            
            await conn.execute('''
                INSERT INTO users (nama_lengkap, username, email, password_hash, salt, role, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', 
                app_config.DEFAULT_ADMIN_USERNAME,  # nama_lengkap
                app_config.DEFAULT_ADMIN_USERNAME,  # username
                app_config.DEFAULT_ADMIN_EMAIL,     # email
                password_hash,                      # password_hash
                salt,                              # salt
                'superadmin',                      # role
                True                               # is_active
            )
            
            logger.info(f"Default admin user '{app_config.DEFAULT_ADMIN_USERNAME}' created successfully")
            
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate key" in str(e).lower():
                logger.info(f"Admin user already exists, skipping creation")
            else:
                logger.error(f"Failed to create default admin: {e}")
        finally:
            if conn:
                await self.pool.release(conn)

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using PBKDF2"""
        import hashlib
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

    def _verify_password(self, password: str, salt: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password, salt) == password_hash

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        if not self.pool:
            logger.error("Database pool not initialized")
            return None
            
        conn = None
        try:
            # Ensure pool is properly initialized
            if not self._initialized:
                await self.initialize()
            
            conn = await self.pool.acquire()
            
            # Set connection timeout
            await conn.execute("SET statement_timeout = '10s'")
            
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE username = $1 AND is_active = true",
                username
            )
            
            if row and self._verify_password(password, row['salt'], row['password_hash']):
                # Update last login in a separate transaction to avoid blocking
                try:
                    await conn.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
                        row['id']
                    )
                except Exception as login_update_error:
                    logger.warning(f"Failed to update last login for user {username}: {login_update_error}")
                
                return User(**dict(row))
            return None
            
        except asyncio.TimeoutError:
            logger.error(f"Authentication timeout for user {username}")
            return None
        except asyncpg.ConnectionDoesNotExistError:
            logger.error(f"Database connection lost during authentication for user {username}")
            return None
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {e}")
            return None
        finally:
            if conn:
                try:
                    await self.pool.release(conn)
                except asyncpg.ConnectionDoesNotExistError:
                    logger.warning("Connection was already closed when trying to release")
                except Exception as release_error:
                    logger.warning(f"Error releasing connection: {release_error}")

    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create new user"""
        conn = None
        try:
            conn = await self.pool.acquire()
            
            # Generate salt and hash password
            salt = secrets.token_hex(32)
            password_hash = self._hash_password(user_data['password'], salt)
            
            user_id = await conn.fetchval('''
                INSERT INTO users (nama_lengkap, username, email, password_hash, salt, role, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            ''', 
                user_data.get('nama_lengkap', ''),
                user_data['username'],
                user_data['email'],
                password_hash,
                salt,
                user_data.get('role', 'user'),
                user_data.get('is_active', True)
            )
            
            # Return created user
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            return User(**dict(row))
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
        finally:
            if conn:
                await self.pool.release(conn)

    async def list_users(self) -> List[User]:
        """List all users"""
        conn = None
        try:
            conn = await self.pool.acquire()
            rows = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC")
            return [User(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []
        finally:
            if conn:
                await self.pool.release(conn)

    async def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        conn = None
        try:
            conn = await self.pool.acquire()
            
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            active_users = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = true")
            superadmins = await conn.fetchval("SELECT COUNT(*) FROM users WHERE role = 'superadmin'")
            recent_logins = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE last_login > CURRENT_TIMESTAMP - INTERVAL '7 days'"
            )
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'superadmins': superadmins,
                'recent_logins': recent_logins
            }
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {}
        finally:
            if conn:
                await self.pool.release(conn)

    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        conn = None
        try:
            conn = await self.pool.acquire()
            await conn.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
                user_id
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update last login: {e}")
            return False
        finally:
            if conn:
                await self.pool.release(conn)

    async def log_audit(self, user_id: str, action: str, resource: str, 
                       details: dict = None, ip_address: str = None, 
                       user_agent: str = None) -> bool:
        """Log audit event"""
        conn = None
        try:
            conn = await self.pool.acquire()
            await conn.execute('''
                INSERT INTO audit_logs (user_id, action, resource, details, ip_address, user_agent)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', user_id, action, resource, json.dumps(details or {}), ip_address, user_agent)
            return True
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False
        finally:
            if conn:
                await self.pool.release(conn)


# Global database manager instance
db_manager = None

async def init_database():
    """Initialize database connection"""
    global db_manager
    from .config import config as app_config
    
    # Create PostgreSQL manager with config
    postgres_config = app_config.get_postgres_config()
    db_manager = PostgreSQLManager(config=postgres_config)
    await db_manager.initialize()
    return db_manager

async def close_database():
    """Close database connection"""
    global db_manager
    if db_manager:
        await db_manager.close()
        db_manager = None

def get_db_manager() -> PostgreSQLManager:
    """Get database manager instance with lazy initialization"""
    global db_manager
    if db_manager is None:
        try:
            from .config import config as app_config
            db_manager = PostgreSQLManager(config=app_config.get_postgres_config())
            logger.info(f"Database manager created with config from .env")
        except Exception as e:
            logger.warning(f"Database manager initialization deferred: {e}")
            # Return None instead of placeholder to avoid further errors
            return None
    return db_manager

async def ensure_db_initialized():
    """Ensure database is initialized, with retry logic"""
    global db_manager
    if db_manager is None or db_manager.pool is None:
        try:
            await init_database()
        except Exception as e:
            logger.error(f"Failed to ensure database initialization: {e}")
            return False
    return True
