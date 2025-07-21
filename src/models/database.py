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
    """PostgreSQL Database Manager"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            # Fallback to individual components
            host = os.getenv('POSTGRES_HOST', 'localhost')
            port = os.getenv('POSTGRES_PORT', '5432')
            user = os.getenv('POSTGRES_USER', 'trigger_deploy_user')
            password = os.getenv('POSTGRES_PASSWORD', 'secure_password_123')
            database = os.getenv('POSTGRES_DB', 'trigger_deploy')
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        self.pool = None
        logger.info(f"PostgreSQL Manager initialized with URL: {self.database_url.split('@')[0]}@[REDACTED]")

    async def init_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("PostgreSQL connection pool created successfully")
            await self.create_tables()
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise

    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    async def create_tables(self):
        """Create database tables"""
        async with self.pool.acquire() as conn:
            # Users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    nama_lengkap VARCHAR(255) NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('superadmin', 'user')),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP WITH TIME ZONE
                )
            ''')

            # Deployment history table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS deployments (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    service_name VARCHAR(255) NOT NULL,
                    server_name VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    triggered_by VARCHAR(255),
                    command TEXT,
                    output TEXT,
                    error_output TEXT,
                    duration REAL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Audit logs table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id),
                    action VARCHAR(255) NOT NULL,
                    resource VARCHAR(255),
                    details JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_deployments_service ON deployments(service_name)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_deployments_created_at ON deployments(created_at)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)')

            logger.info("Database tables created/verified successfully")

    async def create_default_admin(self):
        """Create default superadmin user if none exists"""
        try:
            async with self.pool.acquire() as conn:
                # Check if any superadmin exists
                result = await conn.fetchval(
                    "SELECT COUNT(*) FROM users WHERE role = 'superadmin'"
                )
                
                if result == 0:
                    # Create default admin
                    salt = secrets.token_hex(32)
                    password_hash = self._hash_password("admin123", salt)
                    
                    await conn.execute('''
                        INSERT INTO users (nama_lengkap, username, email, password_hash, salt, role)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    ''', "Super Administrator", "admin", "admin@trigger-deploy.local", 
                        password_hash, salt, "superadmin")
                    
                    logger.info("Default superadmin user created: admin/admin123")
        except Exception as e:
            logger.error(f"Failed to create default admin: {e}")

    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using PBKDF2"""
        import hashlib
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

    def _verify_password(self, password: str, salt: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password, salt) == password_hash

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE username = $1 AND is_active = true",
                    username
                )
                
                if row and self._verify_password(password, row['salt'], row['password_hash']):
                    # Update last login
                    await conn.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
                        row['id']
                    )
                    
                    return User(**dict(row))
                return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create new user"""
        try:
            salt = secrets.token_hex(32)
            password_hash = self._hash_password(user_data['password'], salt)
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    INSERT INTO users (nama_lengkap, username, email, password_hash, salt, role, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                ''', user_data['nama_lengkap'], user_data['username'], user_data['email'],
                    password_hash, salt, user_data.get('role', 'user'), 
                    user_data.get('is_active', True))
                
                return User(**dict(row))
        except asyncpg.UniqueViolationError as e:
            if 'username' in str(e):
                raise ValueError("Username already exists")
            elif 'email' in str(e):
                raise ValueError("Email already exists")
            else:
                raise ValueError("User already exists")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
                return User(**dict(row)) if row else None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
                return User(**dict(row)) if row else None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None

    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> User:
        """Update user"""
        try:
            # Build dynamic update query
            update_fields = []
            values = []
            param_count = 1
            
            for field in ['nama_lengkap', 'username', 'email', 'role', 'is_active']:
                if field in user_data:
                    update_fields.append(f"{field} = ${param_count}")
                    values.append(user_data[field])
                    param_count += 1
            
            if not update_fields:
                raise ValueError("No fields to update")
            
            update_fields.append(f"updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ${param_count} RETURNING *"
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *values)
                if not row:
                    raise ValueError("User not found")
                return User(**dict(row))
        except asyncpg.UniqueViolationError as e:
            if 'username' in str(e):
                raise ValueError("Username already exists")
            elif 'email' in str(e):
                raise ValueError("Email already exists")
            else:
                raise ValueError("Duplicate value")
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise

    async def update_user_password(self, user_id: str, new_password: str) -> bool:
        """Update user password"""
        try:
            salt = secrets.token_hex(32)
            password_hash = self._hash_password(new_password, salt)
            
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "UPDATE users SET password_hash = $1, salt = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $3",
                    password_hash, salt, user_id
                )
                return result == "UPDATE 1"
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            return False

    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("DELETE FROM users WHERE id = $1", user_id)
                return result == "DELETE 1"
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                    limit, offset
                )
                return [User(**dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    async def get_user_stats(self) -> Dict[str, int]:
        """Get user statistics"""
        try:
            async with self.pool.acquire() as conn:
                total = await conn.fetchval("SELECT COUNT(*) FROM users")
                active = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = true")
                superadmins = await conn.fetchval("SELECT COUNT(*) FROM users WHERE role = 'superadmin'")
                
                return {
                    'total': total,
                    'active': active,
                    'inactive': total - active,
                    'superadmins': superadmins,
                    'users': total - superadmins
                }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'total': 0, 'active': 0, 'inactive': 0, 'superadmins': 0, 'users': 0}

    async def log_audit(self, user_id: str, action: str, resource: str = None, 
                       details: Dict = None, ip_address: str = None, user_agent: str = None):
        """Log audit event"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO audit_logs (user_id, action, resource, details, ip_address, user_agent)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', user_id, action, resource, json.dumps(details) if details else None,
                    ip_address, user_agent)
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")


# Global database manager instance
db_manager = None

async def init_database():
    """Initialize database connection"""
    global db_manager
    db_manager = PostgreSQLManager()
    await db_manager.init_pool()
    await db_manager.create_default_admin()
    return db_manager

async def close_database():
    """Close database connection"""
    global db_manager
    if db_manager:
        await db_manager.close_pool()

def get_db_manager() -> PostgreSQLManager:
    """Get database manager instance"""
    global db_manager
    if not db_manager:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db_manager
