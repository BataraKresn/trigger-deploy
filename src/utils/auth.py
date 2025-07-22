# =================================
# Authentication Middleware
# =================================

from functools import wraps
from flask import request, redirect, url_for, session, jsonify
import jwt
import logging
from datetime import datetime, timedelta
from src.models.config import config

logger = logging.getLogger(__name__)


def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not is_authenticated():
            logger.warning(f"Unauthorized access attempt to {request.endpoint} from {request.remote_addr}")
            
            # For AJAX requests, return JSON
            if request.is_json or request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource',
                    'redirect': '/login'
                }), 401
            
            # For regular requests, redirect to login
            return redirect(url_for('main.login', error='Please log in to access this page'))
        
        return f(*args, **kwargs)
    return decorated_function


def is_authenticated():
    """Check if user is authenticated"""
    # Check session first
    if session.get('authenticated'):
        # Validate session hasn't expired
        login_time = session.get('login_time')
        if login_time:
            try:
                login_dt = datetime.fromisoformat(login_time)
                # Check if session is older than 24 hours
                if datetime.now() - login_dt > timedelta(hours=24):
                    session.clear()
                    return False
            except:
                session.clear()
                return False
        return True
    
    # Check JWT token in Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, config.JWT_SECRET or 'default-secret', algorithms=['HS256'])
            # Check if token is expired
            exp = payload.get('exp')
            if exp and datetime.utcnow().timestamp() > exp:
                return False
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            pass
    
    # Check for deploy token
    deploy_token = request.headers.get('X-Deploy-Token') or request.form.get('token')
    if deploy_token == config.TOKEN:
        return True
    
    return False


def get_current_user():
    """Get current authenticated user info"""
    if session.get('authenticated'):
        return {
            'username': session.get('username', 'admin'),
            'role': session.get('role', 'admin'),
            'auth_method': 'session'
        }
    
    # Check JWT token
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, config.JWT_SECRET or 'default-secret', algorithms=['HS256'])
            return {
                'username': payload.get('username', 'admin'),
                'role': payload.get('role', 'admin'),
                'auth_method': 'jwt'
            }
        except jwt.InvalidTokenError:
            pass
    
    return None


def login_user(username, remember_me=False, role='admin'):
    """Login user and create session"""
    session.permanent = remember_me
    session['authenticated'] = True
    session['username'] = username
    session['role'] = role
    session['login_time'] = datetime.now().isoformat()
    
    logger.info(f"User {username} logged in successfully with role {role}")
    return True


def logout_user():
    """Logout user and clear session"""
    session.clear()
    return True
