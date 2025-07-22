# =================================
# Main Web Routes - Updated with proper auth flow
# =================================

from flask import Blueprint, render_template, request, jsonify, send_from_directory, session, redirect, url_for, flash
import os
import json
import re
import logging
from datetime import datetime
from src.utils.helpers import load_servers, validate_token, is_valid_server
from src.models.config import config
from src.utils.auth import require_auth, is_authenticated, logout_user

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def landing():
    """Landing page - always accessible. Shows welcome page."""
    return render_template('landing.html')


@main_bp.route('/home')
def home():
    """Redirect /home to /dashboard for consistency"""
    return redirect(url_for('main.dashboard'))


@main_bp.route('/dashboard')
@require_auth
def dashboard():
    """Dashboard page - requires authentication"""
    authenticated = is_authenticated()
    return render_template('home.html', authenticated=authenticated)


@main_bp.route('/login')
def login():
    """Login page"""
    # If user is already authenticated, redirect to dashboard
    if is_authenticated():
        return redirect(url_for('main.dashboard'))
    
    # Get any messages from URL params
    message = request.args.get('message', '')
    error = request.args.get('error', '')
    
    return render_template('login.html', message=message, error=error)


@main_bp.route('/deploy-servers')
@require_auth
def deploy_servers():
    """Deploy servers page"""
    authenticated = is_authenticated()
    return render_template('deploy_servers.html', authenticated=authenticated)


@main_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0"
    })


@main_bp.route('/help')
def help_page():
    """Help page"""
    return render_template('help.html')


@main_bp.route('/auth/logout', methods=['GET', 'POST'])
def logout():
    """Handle logout"""
    try:
        # Clear session if authenticated
        if is_authenticated():
            logout_user()
        
        # Handle JSON requests (AJAX)
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': True,
                'message': 'Successfully logged out',
                'redirect': url_for('main.login')
            })
        
        # Handle regular requests
        return redirect(url_for('main.login', message='Successfully logged out'))
    except Exception as e:
        logger.error(f"Logout error: {e}")
        
        # Handle JSON requests (AJAX)
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': False,
                'message': 'Logout failed',
                'error': str(e)
            }), 500
        
        return redirect(url_for('main.login', error='Logout failed'))


@main_bp.route('/users')
@require_auth
def users():
    """User management page - requires authentication"""
    authenticated = is_authenticated()
    return render_template('user_management.html', authenticated=authenticated)


@main_bp.route('/metrics')
@require_auth
def metrics():
    """Metrics dashboard page - requires authentication"""
    authenticated = is_authenticated()
    return render_template('metrics.html', authenticated=authenticated)


@main_bp.route('/services-monitor')
@require_auth
def services_monitor():
    """Services monitoring page - requires authentication"""
    authenticated = is_authenticated()
    return render_template('services_monitor.html', authenticated=authenticated)


@main_bp.route('/docs')
def docs():
    """API documentation page"""
    authenticated = is_authenticated()
    return render_template('docs.html', authenticated=authenticated)


@main_bp.route('/api/docs')
def api_docs():
    """Redirect /api/docs to docs page"""
    return redirect(url_for('main.docs'))


@main_bp.route('/api/docs/')
def api_docs_slash():
    """Redirect /api/docs/ to docs page"""
    return redirect(url_for('main.docs'))


@main_bp.route('/help')
def help_center():
    """Help center page"""
    return render_template('help.html')


@main_bp.route('/analytics')
@require_auth
def analytics():
    """Analytics dashboard - requires authentication"""
    return render_template('analytics.html')


@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')


@main_bp.route('/contact-messages')
@require_auth
def contact_messages():
    """View contact messages - requires authentication"""
    try:
        import asyncio
        from src.models.contact_manager import get_contact_manager
        
        async def get_messages():
            contact_manager = get_contact_manager()
            if contact_manager:
                return await contact_manager.get_all_messages()
            return []
        
        messages = asyncio.run(get_messages())
        return render_template('contact_messages.html', 
                             contact_messages=messages,
                             current_page='contact')
        
    except Exception as e:
        logger.error(f"Error loading contact messages: {e}")
        return render_template('contact_messages.html', 
                             contact_messages=[],
                             current_page='contact',
                             error="Could not load messages")


@main_bp.route('/api/contact', methods=['POST'])
def submit_contact():
    """Handle contact form submission via API"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['name', 'email', 'message']):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        import asyncio
        from src.models.contact_manager import get_contact_manager
        
        async def save_message():
            contact_manager = get_contact_manager()
            if contact_manager:
                return await contact_manager.add_message(
                    name=data['name'],
                    email=data['email'],
                    subject=data.get('subject', 'Contact Form'),
                    message=data['message']
                )
            return False
        
        success = asyncio.run(save_message())
        
        if success:
            return jsonify({'success': True, 'message': 'Message sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to save message'}), 500
            
    except Exception as e:
        logger.error(f"Contact submission error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500


@main_bp.route('/api/contact/count', methods=['GET'])
@require_auth  
def get_unread_contact_count():
    """Get unread contact messages count"""
    import asyncio
    from src.models.contact_manager import get_contact_manager
    
    try:
        async def get_count():
            contact_manager = get_contact_manager()
            if contact_manager:
                return await contact_manager.get_unread_count()
            return 0
        
        count = asyncio.run(get_count())
        return jsonify({'count': count})
        
    except Exception as e:
        return jsonify({'count': 0, 'error': str(e)})


@main_bp.route('/api')
def api_redirect():
    """Redirect /api to Swagger UI docs"""
    return redirect(url_for('main.docs'))


@main_bp.route('/docs/swagger')
def swagger_ui():
    """Swagger UI for API documentation"""
    authenticated = is_authenticated()
    return render_template('swagger_ui.html', authenticated=authenticated)


@main_bp.route('/openapi.json')
def openapi_spec():
    """Serve OpenAPI specification"""
    return send_from_directory('static', 'openapi.json', mimetype='application/json')


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
