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
    return render_template('home.html')


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


@main_bp.route('/logout')
def logout():
    """Logout endpoint"""
    logout_user()
    return redirect(url_for('main.login', message='Successfully logged out'))


@main_bp.route('/deploy-servers')
@require_auth
def deploy_servers():
    """Deploy servers page - requires authentication"""
    return render_template('deploy_servers.html')


@main_bp.route('/logout')
def logout_get():
    """Logout page (GET request) - redirects to proper logout"""
    return redirect(url_for('main.logout_post'))


@main_bp.route('/logout', methods=['POST'])
def logout_post():
    """Logout POST handler"""
    try:
        from ..utils.auth import logout_user, is_authenticated
        
        if is_authenticated():
            logout_user()
        
        return redirect(url_for('main.login', message='Successfully logged out'))
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return redirect(url_for('main.login', error='Logout failed'))


@main_bp.route('/users')
@require_auth
def users():
    """User management page - requires authentication"""
    return render_template('user_management.html')


@main_bp.route('/metrics')
@require_auth
def metrics():
    """Metrics dashboard page - requires authentication"""
    return render_template('metrics.html')


@main_bp.route('/services-monitor')
@require_auth
def services_monitor():
    """Services monitor page - requires authentication"""
    return render_template('services_monitor.html')


@main_bp.route('/docs')
def docs():
    """API documentation page"""
    return render_template('docs.html')


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
    """Help Center page"""
    return render_template('help.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact Us page"""
    if request.method == 'POST':
        import asyncio
        from src.models.contact_manager import get_contact_manager
        
        try:
            # Get form data
            data = request.get_json() if request.is_json else request.form
            
            first_name = data.get('firstName', '').strip()
            last_name = data.get('lastName', '').strip()
            email = data.get('email', '').strip()
            company = data.get('company', '').strip()
            subject = data.get('subject', '').strip()
            message = data.get('message', '').strip()
            
            # Basic validation
            if not all([first_name, last_name, email, subject, message]):
                return jsonify({
                    'success': False,
                    'message': 'All required fields must be filled'
                }), 400
            
            # Email validation (basic)
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_pattern, email):
                return jsonify({
                    'success': False,
                    'message': 'Please enter a valid email address'
                }), 400
            
            # Prepare contact message data
            contact_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'company': company,
                'subject': subject,
                'message': message
            }
            
            # Save to database
            async def save_contact_message():
                try:
                    contact_manager = get_contact_manager()
                    if contact_manager:
                        return await contact_manager.create_message(contact_data)
                    return False
                except Exception as e:
                    print(f"Database save error: {e}")
                    return False
            
            # Run async function
            success = asyncio.run(save_contact_message())
            
            if success:
                # Send email notification
                try:
                    from src.utils.email_notifications import send_contact_notification_email
                    
                    async def send_notification():
                        return await send_contact_notification_email(contact_data)
                    
                    asyncio.run(send_notification())
                except Exception as email_error:
                    print(f"Email notification failed: {email_error}")
                
                return jsonify({
                    'success': True,
                    'message': 'Thank you for your message! We\'ll get back to you within 24 hours.'
                })
            else:
                # Fallback to log file if database fails
                log_dir = 'logs'
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                contact_log_file = os.path.join(log_dir, 'contact_messages.log')
                with open(contact_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{datetime.now().isoformat()} - Contact Form Submission:\n")
                    f.write(f"Name: {first_name} {last_name}\n")
                    f.write(f"Email: {email}\n")
                    f.write(f"Company: {company}\n")
                    f.write(f"Subject: {subject}\n")
                    f.write(f"Message: {message}\n")
                    f.write("-" * 50 + "\n")
                
                return jsonify({
                    'success': True,
                    'message': 'Thank you for your message! We\'ll get back to you within 24 hours.'
                })
            
        except Exception as e:
            print(f"Contact form error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Sorry, there was an error sending your message. Please try again.'
            }), 500
    
    # GET request - show contact page
    return render_template('contact.html')


@main_bp.route('/admin/contact-messages')
@require_auth
def contact_messages():
    """View contact messages (admin only)"""
    import asyncio
    from src.models.contact_manager import get_contact_manager
    
    try:
        async def get_messages():
            contact_manager = get_contact_manager()
            if contact_manager:
                messages = await contact_manager.get_all_messages(limit=50)
                unread_count = await contact_manager.get_unread_count()
                return messages, unread_count
            return [], 0
        
        messages, unread_count = asyncio.run(get_messages())
        
        return render_template('contact_messages.html', 
                             messages=messages, 
                             unread_count=unread_count)
        
    except Exception as e:
        print(f"Error fetching contact messages: {e}")
        # Fallback to log file
        try:
            contact_log_file = os.path.join('logs', 'contact_messages.log')
            if os.path.exists(contact_log_file):
                with open(contact_log_file, 'r', encoding='utf-8') as f:
                    messages = f.read()
                return f"<pre style='white-space: pre-wrap; font-family: monospace; padding: 20px;'>{messages}</pre>"
            else:
                return "<p>No contact messages found.</p>"
        except Exception as fallback_error:
            return f"<p>Error reading contact messages: {str(fallback_error)}</p>"


@main_bp.route('/api/contact-messages/mark-read/<message_id>', methods=['POST'])
@require_auth
def mark_contact_read(message_id):
    """Mark contact message as read"""
    import asyncio
    from src.models.contact_manager import get_contact_manager
    
    try:
        async def mark_read():
            contact_manager = get_contact_manager()
            if contact_manager:
                return await contact_manager.mark_as_read(message_id)
            return False
        
        success = asyncio.run(mark_read())
        
        if success:
            return jsonify({'success': True, 'message': 'Message marked as read'})
        else:
            return jsonify({'success': False, 'message': 'Failed to mark message as read'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@main_bp.route('/api/contact-messages/unread-count')
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
