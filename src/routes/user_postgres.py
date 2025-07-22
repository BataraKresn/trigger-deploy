"""
User Routes with PostgreSQL support
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
import jwt
import logging
from typing import Optional

from ..models.database import get_db_manager

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/api')

@user_bp.route('/login', methods=['POST'])
def login():
    """User login with PostgreSQL"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        remember_me = data.get('remember_me', False)
        
        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400
        
        db = get_db_manager()
        if not db:
            logger.error("Database manager not available")
            return jsonify({'message': 'Database connection unavailable'}), 500
        
        # Check database health
        if not db.health_check():
            logger.warning("Database connection unhealthy")
            return jsonify({'message': 'Database connection error'}), 500
        
        # Authenticate user (now sync operation)
        try:
            user = db.authenticate_user(username, password)
        except Exception as auth_error:
            logger.error(f"Authentication error: {auth_error}")
            return jsonify({'message': 'Authentication failed'}), 500
        
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'message': 'Account is disabled'}), 401
        
        # Update last login (non-blocking)
        try:
            db.update_last_login(user.id)
        except Exception as e:
            logger.warning(f"Failed to update last login: {e}")
        
        # Create Flask session
        from ..utils.auth import login_user
        login_user(user.username, remember_me, user.role)
        
        # Generate JWT token
        from ..models.config import config
        import jwt
        from datetime import datetime, timedelta
        
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        try:
            token = jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')
        except Exception as token_error:
            logger.warning(f"Failed to create JWT token: {token_error}")
            token = None
        
        # Log audit event (non-blocking)
        try:
            db.log_audit(
                user_id=user.id,
                action='LOGIN',
                resource='auth',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        except Exception as audit_error:
            logger.warning(f"Failed to log audit: {audit_error}")
        
        response_data = {
            'success': True,
            'user': user.to_safe_dict(),
            'message': 'Login successful',
            'redirect': '/dashboard'  # Add explicit redirect URL
        }
        
        if token:
            response_data['token'] = token
            
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({'message': 'Login failed'}), 500


@user_bp.route('/logout', methods=['POST'])
def logout():
    """User logout"""
    try:
        # Clear Flask session
        from ..utils.auth import logout_user
        logout_user()
        
        # Log audit event if user was authenticated
        if session.get('username'):
            try:
                db = get_db_manager()
                if db:
                    # Get user ID for audit log
                    user = db.get_user_by_username(session.get('username'))
                    if user:
                        db.log_audit(
                            user_id=user.id,
                            action='LOGOUT',
                            resource='auth',
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent')
                        )
            except Exception as audit_error:
                logger.warning(f"Failed to log logout audit: {audit_error}")
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'redirect': '/login'
        })
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({'message': 'Logout failed'}), 500

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
            from ..models.config import config
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
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

# run_async function removed - now using sync database operations

@user_bp.route('/users', methods=['GET'])
@require_auth
@require_superadmin
def list_users():
    """List all users - superadmin only"""
    try:
        db = get_db_manager()
        users = db.list_users()
        stats = db.get_user_stats()
        
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
        user = db.create_user(data)

        # Log audit
        db.log_audit(
            user_id=request.current_user['user_id'],
            action='CREATE_USER',
            resource=f'user:{user.username}',
            details={'created_user_id': str(user.id)},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
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
        user = db.get_user_by_id(user_id)
        
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
        user = db.update_user(user_id, data)
        
        # Log audit event
        db.log_audit(
            user_id=request.current_user['user_id'],
            action='UPDATE_USER',
            resource=f'user:{user.username}',
            details={'updated_fields': list(data.keys())},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
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
        success = db.update_user_password(user_id, new_password)
        
        if not success:
            return jsonify({'message': 'User not found'}), 404
        
        # Log audit event
        db.log_audit(
            user_id=request.current_user['user_id'],
            action='CHANGE_PASSWORD',
            resource=f'user:{user_id}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
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
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        success = db.delete_user(user_id)
        
        if not success:
            return jsonify({'message': 'User not found'}), 404
        
        # Log audit event
        db.log_audit(
            user_id=request.current_user['user_id'],
            action='DELETE_USER',
            resource=f'user:{user.username}',
            details={'deleted_user_id': user_id},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
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
        stats = db.get_user_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'message': 'Failed to get user stats'}), 500
