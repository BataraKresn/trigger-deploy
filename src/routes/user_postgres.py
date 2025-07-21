"""
User Routes with PostgreSQL support
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
import jwt
import asyncio
import logging
from typing import Optional

from ..models.database import get_db_manager

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/api')

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Authentication required'}), 401
        
        try:
            # Decode JWT token
            from ..models.config import get_config
            config = get_config()
            payload = jwt.decode(token, config.jwt_secret, algorithms=['HS256'])
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_superadmin(f):
    """Decorator to require superadmin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user.get('role') != 'superadmin':
            return jsonify({'message': 'Superadmin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

async def run_async(coro):
    """Helper to run async functions in sync context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return await coro

@user_bp.route('/users', methods=['GET'])
@require_auth
@require_superadmin
def list_users():
    """List all users"""
    try:
        db = get_db_manager()
        users = asyncio.run(db.list_users())
        stats = asyncio.run(db.get_user_stats())
        
        return jsonify({
            'users': [user.to_safe_dict() for user in users],
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({'message': 'Failed to list users'}), 500

@user_bp.route('/users', methods=['POST'])
@require_auth
@require_superadmin
def create_user():
    """Create new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['nama_lengkap', 'username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Validate password length
        if len(data['password']) < 6:
            return jsonify({'message': 'Password must be at least 6 characters long'}), 400
        
        # Validate email format
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, data['email']):
            return jsonify({'message': 'Invalid email format'}), 400
        
        db = get_db_manager()
        user = asyncio.run(db.create_user(data))
        
        # Log audit event
        asyncio.run(db.log_audit(
            user_id=request.current_user['user_id'],
            action='CREATE_USER',
            resource=f'user:{user.username}',
            details={'created_user_id': str(user.id)},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        ))
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_safe_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({'message': 'Failed to create user'}), 500

@user_bp.route('/users/<user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """Get user by ID"""
    try:
        # Users can only view their own profile unless they're superadmin
        if (request.current_user.get('role') != 'superadmin' and 
            request.current_user.get('user_id') != user_id):
            return jsonify({'message': 'Access denied'}), 403
        
        db = get_db_manager()
        user = asyncio.run(db.get_user_by_id(user_id))
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({'user': user.to_safe_dict()})
        
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return jsonify({'message': 'Failed to get user'}), 500

@user_bp.route('/users/<user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    """Update user"""
    try:
        # Users can only update their own profile unless they're superadmin
        if (request.current_user.get('role') != 'superadmin' and 
            request.current_user.get('user_id') != user_id):
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Non-superadmins cannot change role
        if (request.current_user.get('role') != 'superadmin' and 'role' in data):
            data.pop('role')
        
        # Validate email format if provided
        if 'email' in data:
            import re
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_pattern, data['email']):
                return jsonify({'message': 'Invalid email format'}), 400
        
        db = get_db_manager()
        user = asyncio.run(db.update_user(user_id, data))
        
        # Log audit event
        asyncio.run(db.log_audit(
            user_id=request.current_user['user_id'],
            action='UPDATE_USER',
            resource=f'user:{user.username}',
            details={'updated_fields': list(data.keys())},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        ))
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_safe_dict()
        })
        
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return jsonify({'message': 'Failed to update user'}), 500

@user_bp.route('/users/<user_id>/password', methods=['PUT'])
@require_auth
def update_user_password(user_id):
    """Update user password"""
    try:
        # Users can only change their own password unless they're superadmin
        if (request.current_user.get('role') != 'superadmin' and 
            request.current_user.get('user_id') != user_id):
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        new_password = data.get('password')
        
        if not new_password:
            return jsonify({'message': 'Password is required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'message': 'Password must be at least 6 characters long'}), 400
        
        db = get_db_manager()
        success = asyncio.run(db.update_user_password(user_id, new_password))
        
        if not success:
            return jsonify({'message': 'User not found'}), 404
        
        # Log audit event
        asyncio.run(db.log_audit(
            user_id=request.current_user['user_id'],
            action='CHANGE_PASSWORD',
            resource=f'user:{user_id}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        ))
        
        return jsonify({'message': 'Password updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating password: {e}")
        return jsonify({'message': 'Failed to update password'}), 500

@user_bp.route('/users/<user_id>', methods=['DELETE'])
@require_auth
@require_superadmin
def delete_user(user_id):
    """Delete user"""
    try:
        # Cannot delete yourself
        if request.current_user.get('user_id') == user_id:
            return jsonify({'message': 'Cannot delete yourself'}), 400
        
        db = get_db_manager()
        
        # Get user info for audit log
        user = asyncio.run(db.get_user_by_id(user_id))
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        success = asyncio.run(db.delete_user(user_id))
        
        if not success:
            return jsonify({'message': 'User not found'}), 404
        
        # Log audit event
        asyncio.run(db.log_audit(
            user_id=request.current_user['user_id'],
            action='DELETE_USER',
            resource=f'user:{user.username}',
            details={'deleted_user_id': user_id},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        ))
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return jsonify({'message': 'Failed to delete user'}), 500

@user_bp.route('/users/stats', methods=['GET'])
@require_auth
@require_superadmin
def get_user_stats():
    """Get user statistics"""
    try:
        db = get_db_manager()
        stats = asyncio.run(db.get_user_stats())
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'message': 'Failed to get user stats'}), 500
