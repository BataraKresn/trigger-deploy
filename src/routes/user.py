# =================================
# User Management API Routes
# =================================

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import jwt
import json
from src.models.user import user_manager, User
from src.models.config import config
from functools import wraps


user_bp = Blueprint('user', __name__, url_prefix='/api/users')


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authorization token required'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
            current_user = user_manager.get_user_by_id(payload.get('user_id'))
            if not current_user or not current_user.is_active:
                return jsonify({'error': 'Invalid user'}), 401
            
            request.current_user = current_user
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    
    return decorated_function


def require_superadmin(f):
    """Decorator to require superadmin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user.role != 'superadmin':
            return jsonify({'error': 'Superadmin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated_function


@user_bp.route('/', methods=['GET'])
@require_auth
@require_superadmin
def get_all_users():
    """Get all users (superadmin only)"""
    try:
        users = user_manager.get_all_users()
        return jsonify({
            'success': True,
            'users': [user.to_safe_dict() for user in users]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/<user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """Get specific user"""
    try:
        target_user = user_manager.get_user_by_id(user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check permissions
        if not user_manager.can_user_edit_user(request.current_user, target_user):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'user': target_user.to_safe_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/', methods=['POST'])
@require_auth
@require_superadmin
def create_user():
    """Create new user (superadmin only)"""
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['username', 'email', 'full_name', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Validate role
        role = data.get('role', 'user')
        if role not in ['user', 'superadmin']:
            return jsonify({'success': False, 'error': 'Invalid role'}), 400
        
        # Create user
        user = user_manager.create_user(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            password=data['password'],
            role=role
        )
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': user.to_safe_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/<user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    """Update user"""
    try:
        target_user = user_manager.get_user_by_id(user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check permissions
        if not user_manager.can_user_edit_user(request.current_user, target_user):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Prepare update data
        update_data = {}
        allowed_fields = ['email', 'full_name']
        
        # Only superadmin can change username and role
        if request.current_user.role == 'superadmin':
            allowed_fields.extend(['username', 'role'])
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Update user
        updated_user = user_manager.update_user(user_id, **update_data)
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': updated_user.to_safe_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/<user_id>/password', methods=['PUT'])
@require_auth
def update_user_password(user_id):
    """Update user password"""
    try:
        target_user = user_manager.get_user_by_id(user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check permissions
        if not user_manager.can_user_edit_user(request.current_user, target_user):
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.get_json()
        new_password = data.get('new_password')
        current_password = data.get('current_password')
        
        if not new_password:
            return jsonify({'success': False, 'error': 'New password is required'}), 400
        
        # Verify current password (unless superadmin changing other user's password)
        if request.current_user.id == target_user.id:
            if not current_password:
                return jsonify({'success': False, 'error': 'Current password is required'}), 400
            if not user_manager.verify_password(current_password, target_user.password_hash):
                return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
        
        # Update password
        success = user_manager.update_user_password(user_id, new_password)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Password updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update password'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/<user_id>', methods=['DELETE'])
@require_auth
@require_superadmin
def delete_user(user_id):
    """Delete user (superadmin only)"""
    try:
        # Prevent deleting self
        if request.current_user.id == user_id:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        success = user_manager.delete_user(user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'User deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/profile', methods=['GET'])
@require_auth
def get_current_user_profile():
    """Get current user profile"""
    try:
        return jsonify({
            'success': True,
            'user': request.current_user.to_safe_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
