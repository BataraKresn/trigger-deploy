# =================================
# Main Web Routes
# =================================

from flask import Blueprint, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import os
import json
from src.utils.helpers import load_servers, validate_token, is_valid_server
from src.models.config import config
from src.utils.auth import require_auth, is_authenticated


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def landing():
    """Landing page - always accessible"""
    # If user is already authenticated, redirect to dashboard
    if is_authenticated():
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')


@main_bp.route('/home')
@require_auth
def home():
    """Home page (dashboard)"""
    return render_template('home.html')


@main_bp.route('/dashboard')
@require_auth
def dashboard():
    """Dashboard page (same as home but with explicit route)"""
    return render_template('home.html')


@main_bp.route('/login')
def login():
    """Login page"""
    # If user is already authenticated, redirect to dashboard
    if is_authenticated():
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')
    """Home page (dashboard)"""
    return render_template('home.html')


@main_bp.route('/dashboard')
def dashboard():
    """Dashboard page (same as home but with explicit route)"""
    return render_template('home.html')


@main_bp.route('/login')
def login():
    """Login page"""
    return render_template('login.html')


@main_bp.route('/users')
def users():
    """User management page"""
    return render_template('user_management.html')


@main_bp.route('/deploy-servers')
def deploy_servers():
    """Deploy servers page"""
    return render_template('deploy_servers.html')


@main_bp.route('/metrics')
def metrics():
    """Metrics dashboard page"""
    return render_template('metrics.html')


@main_bp.route('/services-monitor')
def services_monitor():
    """Services monitor page"""
    return render_template('services_monitor.html')


@main_bp.route('/docs')
def docs():
    """API documentation page"""
    return render_template('docs.html')


@main_bp.route('/help')
def help_center():
    """Help Center page"""
    return render_template('help.html')


@main_bp.route('/api')
def api_docs():
    """API Documentation page (alias)"""
    return render_template('docs.html')


@main_bp.route('/invalid-token')
def invalid_token():
    """Invalid token error page"""
    return render_template('invalid_token.html')


@main_bp.route('/trigger-result')
def trigger_result():
    """Deployment result page"""
    log_file = request.args.get('log')
    message = request.args.get('message', 'Deployment completed')
    return render_template('trigger_result.html', log_file=log_file, message=message)


@main_bp.route('/servers', methods=['GET'])
def get_servers():
    """Get list of servers with health status"""
    try:
        servers = load_servers()
        return jsonify([server.to_dict() for server in servers])
    except Exception as e:
        return jsonify({"error": f"Failed to load servers: {str(e)}"}), 500


@main_bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(
        os.path.join('static', 'images'),
        'favicon.ico', 
        mimetype='image/vnd.microsoft.icon'
    )


@main_bp.route('/logs/<path:filename>', methods=['GET'])
def serve_log_file(filename):
    """Serve log files"""
    try:
        log_path = os.path.join(config.LOG_DIR, filename)
        if not os.path.exists(log_path):
            return jsonify({'error': 'Log file not found'}), 404
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        return content, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500
