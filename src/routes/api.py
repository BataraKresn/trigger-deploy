# =================================
# API Routes with PostgreSQL Support
# =================================

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import json
import os
import jwt
import hashlib
import asyncio
from src.utils.helpers import (
    load_servers, load_services, ping_check, 
    dns_resolve_check, http_check
)
from src.models.entities import Server, Service
from src.models.config import config
from src.utils.deployment_history import deployment_history
from src.utils.service_monitor import service_monitor
from src.utils.analytics import DeploymentAnalytics

# Import appropriate user manager
try:
    from src.models.database import get_db_manager
    USING_POSTGRES = True
except ImportError:
    from src.models.user import user_manager
    USING_POSTGRES = False


api_bp = Blueprint('api', __name__, url_prefix='/api')


# Authentication endpoints
@api_bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user with username/password and return JWT token"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request format'}), 400
            
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username:
            return jsonify({'success': False, 'error': 'Username is required'}), 400
            
        if not password:
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        
        # Try user authentication first
        user = None
        if USING_POSTGRES:
            try:
                # For now, use simple file-based auth to avoid async issues
                # PostgreSQL auth can be implemented later with proper async setup
                user = user_manager.authenticate_user(username, password)
            except Exception as e:
                print(f"Authentication error: {e}")
                user = None
        else:
            user = user_manager.authenticate_user(username, password)
            
        if user:
            # Generate JWT token using user data
            payload = {
                'user_id': str(user.id) if USING_POSTGRES else user.id,
                'username': user.username,
                'role': user.role,
                'auth_type': 'user_password',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            
            try:
                token = jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')
                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {
                        'id': user.id,
                        'name': user.full_name,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role
                    },
                    'message': f'Welcome back, {user.full_name}!'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': 'Token generation failed. Please try again.'}), 500
        
        # Fallback to legacy LOGIN_PASSWORD authentication
        elif password == config.LOGIN_PASSWORD:
            # Generate JWT token using legacy method
            payload = {
                'username': username,
                'role': 'admin',
                'auth_type': 'legacy_password',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            
            try:
                token = jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')
                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {
                        'name': username,
                        'username': username,
                        'role': 'admin'
                    },
                    'message': f'Welcome back, {username}! (Legacy Authentication)'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': 'Token generation failed. Please try again.'}), 500
        else:
            # Authentication failed
            return jsonify({
                'success': False, 
                'error': 'Invalid username or password. Please check your credentials and try again.'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': 'An unexpected error occurred. Please try again.'
        }), 500


@api_bp.route('/auth/verify', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'valid': False, 'error': 'No token provided'}), 400
    
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
        return jsonify({
            'valid': True,
            'user': {
                'name': payload.get('username'),
                'role': payload.get('role', 'admin'),
                'auth_type': payload.get('auth_type', 'unknown')
            }
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'error': 'Invalid token'}), 401


@api_bp.route('/auth/token-login', methods=['POST'])
def token_login():
    """Login using deployment token directly (for quick access)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request format'}), 400
            
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'success': False, 'error': 'Deployment token is required'}), 400
        
        # Use deployment token for quick access (this is different from login password)
        if token == config.TOKEN:
            # Generate JWT token
            payload = {
                'username': 'deploy-user',
                'role': 'admin',
                'auth_type': 'deploy_token',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            
            try:
                jwt_token = jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')
                return jsonify({
                    'success': True,
                    'token': jwt_token,
                    'user': {
                        'name': 'Deploy User',
                        'role': 'admin'
                    },
                    'message': 'Quick access granted with deployment token!'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': 'Token generation failed. Please try again.'}), 500
        else:
            return jsonify({
                'success': False, 
                'error': 'Invalid deployment token. Please verify your token and try again.'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': 'An unexpected error occurred. Please try again.'
        }), 500


# Dashboard endpoints
@api_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get deployment history stats
        history = deployment_history.get_recent_deployments(50)
        total_deployments = len(history)
        successful_deployments = len([d for d in history if d.get('status') == 'success'])
        
        # Get server count
        servers = load_servers()
        active_servers = len(servers)
        
        # Get service count (basic implementation)
        try:
            services = load_services()
            running_services = len(services)
        except:
            running_services = 0
        
        return jsonify({
            'totalDeployments': str(total_deployments),
            'successfulDeployments': str(successful_deployments),
            'activeServers': str(active_servers),
            'runningServices': str(running_services)
        })
    except Exception as e:
        return jsonify({
            'totalDeployments': '0',
            'successfulDeployments': '0',
            'activeServers': '0',
            'runningServices': '0'
        })


@api_bp.route('/recent-activity', methods=['GET'])
def get_recent_activity():
    """Get recent deployment activity"""
    try:
        history = deployment_history.get_recent_deployments(10)
        activities = []
        
        for deployment in history:
            activity = {
                'title': f"Deployment to {deployment.get('server', 'Unknown')}",
                'description': deployment.get('details', 'Deployment executed'),
                'type': 'success' if deployment.get('status') == 'success' else 'error',
                'timestamp': deployment.get('timestamp', datetime.now().isoformat())
            }
            activities.append(activity)
        
        return jsonify(activities)
    except Exception as e:
        return jsonify([])


@api_bp.route('/auth/demo-info', methods=['GET'])
def get_demo_info():
    """Get demo credentials info (configurable via SHOW_DEMO_CREDENTIALS)"""
    try:
        # Check if demo credentials should be shown
        show_demo = os.getenv('SHOW_DEMO_CREDENTIALS', 'false').lower() == 'true'
        
        if not show_demo:
            return jsonify({
                'demo_available': False,
                'message': 'Demo credentials are disabled. Set SHOW_DEMO_CREDENTIALS=true to enable.'
            })
        
        # Show example username and indicate where to find actual credentials
        return jsonify({
            'demo_available': True,
            'username_example': 'admin',
            'password_hint': 'Check LOGIN_PASSWORD in your .env file',
            'token_hint': 'Check DEPLOY_TOKEN in your .env file',
            'note': 'Actual values are configured in environment variables'
        })
    except Exception as e:
        return jsonify({
            'demo_available': False,
            'error': 'Unable to retrieve demo information'
        })


@api_bp.route('/health', methods=['POST'])
def health_check():
    """Perform comprehensive health check"""
    data = request.get_json()
    target = data.get('target', 'google.com')
    
    # Perform all checks
    ping_result = ping_check(target)
    dns_result = dns_resolve_check(target)
    http_result = http_check(target)
    
    return jsonify({
        'target': target,
        'timestamp': datetime.now().isoformat(),
        'ping': ping_result['message'],
        'resolve': dns_result['message'],
        'http': http_result['message']
    })


@api_bp.route('/health/system', methods=['GET'])
def system_health():
    """Get system health status"""
    try:
        # Check database connectivity if using PostgreSQL
        db_status = 'healthy'
        if USING_POSTGRES:
            try:
                # Simple database check would go here
                db_status = 'healthy'
            except Exception:
                db_status = 'unhealthy'
        
        # Check disk space, memory, etc.
        import psutil
        disk_usage = psutil.disk_usage('/')
        memory = psutil.virtual_memory()
        
        # Determine overall status
        status = 'healthy'
        if disk_usage.percent > 90 or memory.percent > 90:
            status = 'warning'
        if db_status == 'unhealthy':
            status = 'unhealthy'
            
        return jsonify({
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'components': {
                'database': db_status,
                'disk_usage': f"{disk_usage.percent:.1f}%",
                'memory_usage': f"{memory.percent:.1f}%"
            },
            'version': '2.1.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'version': '2.1.0'
        }), 500


@api_bp.route('/metrics/stats', methods=['GET'])
def get_metrics_stats():
    """Get deployment statistics"""
    try:
        # This would typically come from a database
        # For now, return mock data
        stats = {
            'total': 45,
            'success': 38,
            'failed': 7,
            'success_rate': 84.4,
            'in_progress': 0,
            'uptime': 86400  # 24 hours in seconds
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/metrics/history', methods=['GET'])
def get_deployment_history():
    """Get deployment history"""
    try:
        # Get real deployment history
        deployments = deployment_history.get_all_deployments()
        return jsonify(deployments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/metrics/servers', methods=['GET'])


@api_bp.route('/metrics/servers', methods=['GET'])
def get_server_metrics():
    """Get server statistics"""
    try:
        servers = load_servers()
        server_stats = []
        
        for server in servers:
            server_stats.append({
                'name': server.name,
                'ip': server.ip,
                'status': server.status,
                'type': server.type,
                'last_check': datetime.now().isoformat()
            })
        
        return jsonify({'servers': server_stats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/metrics/system', methods=['GET'])
def get_system_metrics():
    """Get system information"""
    try:
        import psutil
        import platform
        
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'hostname': platform.node(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_total': psutil.virtual_memory().total,
            'memory_used': psutil.virtual_memory().used,
            'memory_percent': psutil.virtual_memory().percent,
            'disk_total': psutil.disk_usage('/').total,
            'disk_used': psutil.disk_usage('/').used,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime': datetime.now().isoformat()
        }
        
        return jsonify(system_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/services/status', methods=['GET'])
def get_services_status():
    """Get status of all monitored services"""
    try:
        local_services = service_monitor.check_all_local_services()
        remote_services = service_monitor.check_all_remote_services()
        
        return jsonify({
            'local_services': local_services,
            'remote_services': remote_services,
            'summary': service_monitor.get_services_summary(),
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/services/check/<service_name>', methods=['POST'])
def check_single_service(service_name):
    """Check status of a single service"""
    try:
        # Check if it's a Docker service
        docker_status = service_monitor.check_docker_service(service_name)
        if docker_status.get('found'):
            return jsonify(docker_status)
        
        # Otherwise check as HTTP service
        services = service_monitor.load_services()
        for service in services:
            if service.get('name') == service_name:
                status = service_monitor.check_http_service(service.get('url', ''))
                return jsonify(status)
        
        return jsonify({'error': 'Service not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/services/config', methods=['GET', 'POST'])
def services_config():
    """Get or update services configuration"""
    if request.method == 'GET':
        try:
            # Return current services configuration
            services = service_monitor.load_services()
            return jsonify(services)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            # Update services configuration
            new_config = request.get_json()
            with open(config.SERVICES_FILE, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            # Reload services in monitor
            service_monitor.services = service_monitor.load_services()
            
            return jsonify({'message': 'Configuration updated successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@api_bp.route('/logs/list', methods=['GET'])
def get_logs_list():
    """Get list of available log files"""
    try:
        log_files = []
        if os.path.exists(config.LOG_DIR):
            for filename in os.listdir(config.LOG_DIR):
                if filename.endswith('.log'):
                    file_path = os.path.join(config.LOG_DIR, filename)
                    stat = os.stat(file_path)
                    log_files.append({
                        'name': filename,
                        'size': f"{stat.st_size / 1024:.1f} KB",
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({'logs': log_files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
