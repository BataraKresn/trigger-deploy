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
                logger.error(f"Database error: {e}")
                return None

    async def close(self):
        """Close connection pool gracefully"""
        if self.pool:
            try:
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

    async def get_connection(self):
        """Get database connection"""
        if not self.pool:
            await self.initialize()
        if self.pool:
            return await self.pool.acquire()
        return None

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
                # Create contact_messages table for contact form
                await conn.execute('''
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
                ''')
                
                # Create users table
                await conn.execute('''
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
                ''')
                
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
        finally:
            if conn:
                await self.pool.release(conn)

    async def _create_default_admin(self):
        """Create default admin user if not exists"""
        pass


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


async def get_db_manager() -> PostgreSQLManager:
    """Get database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = PostgreSQLManager()
        await db_manager.initialize()
    return db_manager


async def init_database():
    """Initialize database"""
    await get_db_manager()


async def close_database():
    """Close database connections"""
    global db_manager
    if db_manager:
        await db_manager.close()
        db_manager = None


def get_contact_manager():
    """Get contact manager instance"""
    global contact_manager, db_manager
    if contact_manager is None and db_manager:
        contact_manager = ContactMessageManager(db_manager)
    return contact_manager
