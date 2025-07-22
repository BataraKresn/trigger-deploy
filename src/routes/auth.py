"""
Enhanced authentication routes for the Flask application
Provides robust login, logout, and session management
"""

from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app
from datetime import datetime, timedelta
import jwt
import logging

from ..models.database import get_db_manager
from ..utils.auth import login_user, logout_user, is_authenticated
from ..models.config import config

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def validate_login_data(data):
    """
    Validate login request data
    
    Args:
        data: Request JSON data
        
    Returns:
        tuple: (is_valid, errors, cleaned_data)
    """
    errors = []
    cleaned_data = {}
    
    if not data:
        errors.append("No data provided")
        return False, errors, cleaned_data
    
    # Validate username/email
    username = data.get('username', '').strip()
    if not username:
        errors.append("Username or email is required")
    else:
        cleaned_data['username'] = username
    
    # Validate password
    password = data.get('password', '')
    if not password:
        errors.append("Password is required")
    elif len(password) < 3:  # Minimum password length
        errors.append("Password is too short")
    else:
        cleaned_data['password'] = password
    
    # Optional remember me
    cleaned_data['remember_me'] = bool(data.get('remember_me', False))
    
    return len(errors) == 0, errors, cleaned_data


def generate_jwt_token(user):
    """
    Generate JWT token for user
    
    Args:
        user: User object
        
    Returns:
        str: JWT token or None if failed
    """
    try:
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')
        return token
    except Exception as e:
        logger.error(f"JWT token generation failed: {e}")
        return None


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Enhanced user login endpoint
    Supports both JSON API and form submission
    """
    try:
        # Get request data (JSON or form)
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Validate input
        is_valid, errors, cleaned_data = validate_login_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        # Get database manager
        db = get_db_manager()
        if not db:
            logger.error("Database manager not available")
            return jsonify({
                'success': False,
                'message': 'Database connection unavailable'
            }), 500
        
        # Check database health
        if not db.health_check():
            logger.warning("Database connection unhealthy")
            return jsonify({
                'success': False,
                'message': 'Database connection error'
            }), 500
        
        # Authenticate user
        try:
            user = db.authenticate_user(cleaned_data['username'], cleaned_data['password'])
        except Exception as auth_error:
            logger.error(f"Authentication error: {auth_error}")
            return jsonify({
                'success': False,
                'message': 'Authentication system error'
            }), 500
        
        if not user:
            logger.warning(f"Failed login attempt for username: {cleaned_data['username']}")
            return jsonify({
                'success': False,
                'message': 'Invalid username/email or password'
            }), 401
        
        if not user.is_active:
            logger.warning(f"Login attempt for disabled account: {user.username}")
            return jsonify({
                'success': False,
                'message': 'Account is disabled'
            }), 401
        
        # Update last login timestamp
        try:
            db.update_last_login(user.id)
        except Exception as e:
            logger.warning(f"Failed to update last login for user {user.id}: {e}")
        
        # Create Flask session
        try:
            login_user(user.username, cleaned_data['remember_me'], user.role)
        except Exception as e:
            logger.error(f"Failed to create Flask session: {e}")
            return jsonify({
                'success': False,
                'message': 'Session creation failed'
            }), 500
        
        # Generate JWT token
        token = generate_jwt_token(user)
        if not token:
            logger.warning(f"JWT token generation failed for user {user.username}")
        
        # Log audit event
        try:
            db.log_audit(
                user_id=user.id,
                action='LOGIN',
                resource='auth',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        except Exception as audit_error:
            logger.warning(f"Failed to log audit event: {audit_error}")
        
        # Prepare response
        response_data = {
            'success': True,
            'message': 'Login successful',
            'user': user.to_safe_dict(),
            'redirect': url_for('main.dashboard')
        }
        
        if token:
            response_data['token'] = token
            response_data['token_expires'] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        
        logger.info(f"Successful login for user: {user.username}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Login endpoint error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    User logout endpoint
    Clears Flask session and invalidates tokens
    """
    try:
        # Get current user info before logout
        username = session.get('username', 'unknown')
        
        # Clear Flask session
        logout_user()
        
        # Log audit event if database is available
        try:
            db = get_db_manager()
            if db and username != 'unknown':
                user = db.get_user_by_username(username)
                if user:
                    db.log_audit(
                        user_id=user.id,
                        action='LOGOUT',
                        resource='auth',
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
        except Exception as audit_error:
            logger.warning(f"Failed to log logout audit event: {audit_error}")
        
        logger.info(f"User logged out: {username}")
        return jsonify({
            'success': True,
            'message': 'Logout successful',
            'redirect': url_for('main.login')
        }), 200
        
    except Exception as e:
        logger.error(f"Logout endpoint error: {e}")
        return jsonify({
            'success': False,
            'message': 'Logout failed'
        }), 500


@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """
    Check authentication status
    
    Returns:
        JSON response with authentication status and user info
    """
    try:
        if is_authenticated():
            username = session.get('username')
            
            # Get user details from database
            db = get_db_manager()
            user = None
            if db and username:
                user = db.get_user_by_username(username)
            
            return jsonify({
                'authenticated': True,
                'user': user.to_safe_dict() if user else {
                    'username': username,
                    'role': session.get('role', 'user')
                },
                'session_expires': session.get('expires'),
            }), 200
        else:
            return jsonify({
                'authenticated': False,
                'message': 'Not authenticated'
            }), 401
            
    except Exception as e:
        logger.error(f"Auth status check error: {e}")
        return jsonify({
            'authenticated': False,
            'error': 'Status check failed'
        }), 500


@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """
    Verify JWT token validity
    
    Returns:
        JSON response with token verification result
    """
    try:
        # Get token from request
        token = None
        
        # Try to get from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Try to get from request body
        if not token and request.is_json:
            data = request.get_json()
            token = data.get('token')
        
        if not token:
            return jsonify({
                'valid': False,
                'message': 'No token provided'
            }), 400
        
        # Verify token
        try:
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
            
            # Check if user still exists and is active
            db = get_db_manager()
            if db:
                user = db.get_user_by_id(payload.get('user_id'))
                if not user or not user.is_active:
                    return jsonify({
                        'valid': False,
                        'message': 'User no longer exists or is inactive'
                    }), 401
            
            return jsonify({
                'valid': True,
                'user': {
                    'user_id': payload.get('user_id'),
                    'username': payload.get('username'),
                    'email': payload.get('email'),
                    'role': payload.get('role')
                },
                'expires': payload.get('exp')
            }), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'valid': False,
                'message': 'Token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'valid': False,
                'message': 'Invalid token'
            }), 401
            
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({
            'valid': False,
            'error': 'Token verification failed'
        }), 500


# Error handlers
@auth_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': 'Bad request'
    }), 400


@auth_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500
