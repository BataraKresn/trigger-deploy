# =================================
# User Models - SQLAlchemy ORM
# =================================

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash

from .database import Base
from .config import config


class User(Base):
    """
    SQLAlchemy ORM User model for authentication and authorization
    """
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}  # Allow table redefinition
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User credentials
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User information
    full_name = Column(String(200), nullable=True)
    role = Column(String(20), default='user', nullable=False)  # 'superadmin', 'admin', 'user'
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', role='{self.role}')>"
    
    def set_password(self, password: str):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary (without password)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
    
    def to_safe_dict(self) -> Dict:
        """Convert user to safe dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges"""
        return self.role in ['admin', 'superadmin']
    
    def is_superadmin(self) -> bool:
        """Check if user is superadmin"""
        return self.role == 'superadmin'
