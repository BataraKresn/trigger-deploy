"""
Contact Message Manager for PostgreSQL
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ContactMessageManager:
    """Contact Message management operations"""
    
    def __init__(self, db_manager):
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


# Global contact manager instance
contact_manager = None

def get_contact_manager():
    """Get global contact manager instance"""
    global contact_manager
    from .database import db_manager
    
    if not contact_manager and db_manager:
        contact_manager = ContactMessageManager(db_manager)
    return contact_manager


async def ensure_contact_manager():
    """Ensure contact manager is initialized"""
    global contact_manager
    if not contact_manager:
        from .database import db_manager
        if db_manager:
            contact_manager = ContactMessageManager(db_manager)
    return contact_manager
