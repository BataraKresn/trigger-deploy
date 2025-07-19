from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token
from models.user import User
from utils.auth import check_password, hash_password
from utils.rate_limit import limiter
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

# Create namespace
auth_ns = Namespace('auth', description='Authentication operations')

# API Models for documentation
login_model = auth_ns.model('LoginRequest', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

register_model = auth_ns.model('RegisterRequest', {
    'username': fields.String(required=True, description='Username', min_length=3, max_length=50),
    'password': fields.String(required=True, description='Password', min_length=6),
    'email': fields.String(required=True, description='Email address'),
    'role': fields.String(description='User role', enum=['user', 'admin'], default='user')
})

token_response_model = auth_ns.model('TokenResponse', {
    'access_token': fields.String(description='JWT access token'),
    'refresh_token': fields.String(description='JWT refresh token'),
    'token_type': fields.String(description='Token type', default='Bearer'),
    'expires_in': fields.Integer(description='Token expiration time in seconds')
})

user_info_model = auth_ns.model('UserInfo', {
    'id': fields.Integer(description='User ID'),
    'username': fields.String(description='Username'),
    'email': fields.String(description='Email address'),
    'role': fields.String(description='User role'),
    'created_at': fields.DateTime(description='Account creation date'),
    'last_login': fields.DateTime(description='Last login date')
})

change_password_model = auth_ns.model('ChangePasswordRequest', {
    'current_password': fields.String(required=True, description='Current password'),
    'new_password': fields.String(required=True, description='New password', min_length=6)
})

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('user_login')
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_response_model)
    @limiter.limit("5 per minute")
    def post(self):
        """User login"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                auth_ns.abort(400, "Username and password are required")
            
            # Find user
            user = User.find_by_username(username)
            if not user or not check_password(password, user.password_hash):
                auth_ns.abort(401, "Invalid credentials")
            
            # Update last login
            user.update_last_login()
            
            # Create tokens
            access_token = create_access_token(
                identity=user.id,
                expires_delta=timedelta(hours=1)
            )
            refresh_token = create_refresh_token(
                identity=user.id,
                expires_delta=timedelta(days=30)
            )
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 3600
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            auth_ns.abort(500, f"Login failed: {str(e)}")

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.doc('user_register')
    @auth_ns.expect(register_model)
    @auth_ns.marshal_with(user_info_model, code=201)
    @limiter.limit("3 per minute")
    def post(self):
        """User registration"""
        try:
            data = request.get_json()
            
            # Validate required fields
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            role = data.get('role', 'user')
            
            if not username or not password or not email:
                auth_ns.abort(400, "Username, password, and email are required")
            
            # Check if user already exists
            if User.find_by_username(username):
                auth_ns.abort(400, "Username already exists")
            
            if User.find_by_email(email):
                auth_ns.abort(400, "Email already exists")
            
            # Create user
            user = User.create_user(
                username=username,
                password=password,
                email=email,
                role=role
            )
            
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at
            }, 201
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            auth_ns.abort(500, f"Registration failed: {str(e)}")

@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @auth_ns.doc('refresh_token')
    @auth_ns.marshal_with(token_response_model)
    @jwt_required(refresh=True)
    def post(self):
        """Refresh access token"""
        try:
            current_user_id = get_jwt_identity()
            
            # Create new access token
            new_token = create_access_token(
                identity=current_user_id,
                expires_delta=timedelta(hours=1)
            )
            
            return {
                'access_token': new_token,
                'token_type': 'Bearer',
                'expires_in': 3600
            }
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            auth_ns.abort(500, f"Token refresh failed: {str(e)}")

@auth_ns.route('/me')
class UserProfile(Resource):
    @auth_ns.doc('get_user_profile')
    @auth_ns.marshal_with(user_info_model)
    @jwt_required()
    def get(self):
        """Get current user profile"""
        try:
            current_user_id = get_jwt_identity()
            user = User.find_by_id(current_user_id)
            
            if not user:
                auth_ns.abort(404, "User not found")
            
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at,
                'last_login': user.last_login
            }
            
        except Exception as e:
            logger.error(f"Profile error: {str(e)}")
            auth_ns.abort(500, f"Failed to get profile: {str(e)}")

@auth_ns.route('/change-password')
class ChangePassword(Resource):
    @auth_ns.doc('change_password')
    @auth_ns.expect(change_password_model)
    @jwt_required()
    def post(self):
        """Change user password"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            
            if not current_password or not new_password:
                auth_ns.abort(400, "Current password and new password are required")
            
            user = User.find_by_id(current_user_id)
            if not user:
                auth_ns.abort(404, "User not found")
            
            # Verify current password
            if not check_password(current_password, user.password_hash):
                auth_ns.abort(400, "Current password is incorrect")
            
            # Update password
            user.password_hash = hash_password(new_password)
            user.save()
            
            return {"message": "Password changed successfully"}
            
        except Exception as e:
            logger.error(f"Password change error: {str(e)}")
            auth_ns.abort(500, f"Password change failed: {str(e)}")

@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc('user_logout')
    @jwt_required()
    def post(self):
        """User logout (invalidate token)"""
        try:
            # In a production environment, you would typically:
            # 1. Add token to blacklist
            # 2. Store blacklisted tokens in Redis or database
            # For now, we'll just return success
            
            return {"message": "Successfully logged out"}
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            auth_ns.abort(500, f"Logout failed: {str(e)}")
