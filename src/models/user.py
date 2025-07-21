# =================================
# User Models
# =================================

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import os
from src.models.config import config


@dataclass
class User:
    """User model for authentication and authorization"""
    
    id: str
    username: str
    email: str
    full_name: str
    password_hash: str
    role: str  # 'superadmin' or 'user'
    created_at: str
    updated_at: str
    last_login: Optional[str] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary (without password)"""
        data = asdict(self)
        data.pop('password_hash', None)  # Never expose password hash
        return data
    
    def to_safe_dict(self) -> Dict:
        """Convert user to safe dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login,
            'created_at': self.created_at
        }


class UserManager:
    """User management operations"""
    
    def __init__(self):
        self.users_file = "config/users.json"
        self.ensure_users_file()
        self.create_default_superadmin()
    
    def ensure_users_file(self):
        """Ensure users.json file exists"""
        if not os.path.exists(self.users_file):
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            with open(self.users_file, 'w') as f:
                json.dump([], f, indent=2)
    
    def create_default_superadmin(self):
        """Create default superadmin if no users exist"""
        users = self.load_users()
        if not users:
            default_admin = User(
                id=self.generate_user_id(),
                username="admin",
                email="admin@localhost",
                full_name="System Administrator",
                password_hash=self.hash_password("admin123"),  # Default password
                role="superadmin",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                is_active=True
            )
            self.save_user(default_admin)
    
    def generate_user_id(self) -> str:
        """Generate unique user ID"""
        return secrets.token_urlsafe(8)
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode(), 
                                          salt.encode(), 
                                          100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac('sha256',
                                                    password.encode(),
                                                    salt.encode(),
                                                    100000)
            return stored_hash == password_hash_check.hex()
        except:
            return False
    
    def load_users(self) -> List[User]:
        """Load all users from file"""
        try:
            with open(self.users_file, 'r') as f:
                users_data = json.load(f)
                return [User(**user_data) for user_data in users_data]
        except:
            return []
    
    def save_users(self, users: List[User]):
        """Save all users to file"""
        users_data = [asdict(user) for user in users]
        with open(self.users_file, 'w') as f:
            json.dump(users_data, f, indent=2)
    
    def save_user(self, user: User):
        """Save single user"""
        users = self.load_users()
        # Remove existing user with same ID
        users = [u for u in users if u.id != user.id]
        users.append(user)
        self.save_users(users)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        users = self.load_users()
        for user in users:
            if user.username == username and user.is_active:
                return user
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        users = self.load_users()
        for user in users:
            if user.id == user_id:
                return user
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        if user and self.verify_password(password, user.password_hash):
            # Update last login
            user.last_login = datetime.now().isoformat()
            self.save_user(user)
            return user
        return None
    
    def create_user(self, username: str, email: str, full_name: str, 
                   password: str, role: str = "user") -> User:
        """Create new user"""
        # Check if username already exists
        if self.get_user_by_username(username):
            raise ValueError("Username already exists")
        
        user = User(
            id=self.generate_user_id(),
            username=username,
            email=email,
            full_name=full_name,
            password_hash=self.hash_password(password),
            role=role,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            is_active=True
        )
        
        self.save_user(user)
        return user
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user data"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Update allowed fields
        allowed_fields = ['username', 'email', 'full_name', 'role', 'is_active']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        user.updated_at = datetime.now().isoformat()
        self.save_user(user)
        return user
    
    def update_user_password(self, user_id: str, new_password: str) -> bool:
        """Update user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.password_hash = self.hash_password(new_password)
        user.updated_at = datetime.now().isoformat()
        self.save_user(user)
        return True
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete by setting is_active=False)"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Don't allow deleting the last superadmin
        if user.role == "superadmin":
            active_superadmins = [u for u in self.load_users() 
                                if u.role == "superadmin" and u.is_active]
            if len(active_superadmins) <= 1:
                raise ValueError("Cannot delete the last superadmin")
        
        user.is_active = False
        user.updated_at = datetime.now().isoformat()
        self.save_user(user)
        return True
    
    def get_all_users(self) -> List[User]:
        """Get all active users"""
        users = self.load_users()
        return [user for user in users if user.is_active]
    
    def can_user_manage_users(self, user: User) -> bool:
        """Check if user can manage other users"""
        return user.role == "superadmin"
    
    def can_user_edit_user(self, current_user: User, target_user: User) -> bool:
        """Check if current user can edit target user"""
        # Superadmin can edit anyone
        if current_user.role == "superadmin":
            return True
        # Users can only edit themselves
        return current_user.id == target_user.id


# Global user manager instance
user_manager = UserManager()
