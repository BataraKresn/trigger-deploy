from flask import Flask, request, Response, send_from_directory, jsonify, url_for, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timedelta
from dotenv import load_dotenv
from functools import wraps
from dataclasses import dataclass
import subprocess, os, json
import time
import psutil
import socket
import traceback
import ipaddress
import hashlib
import hmac
import logging
from logging.handlers import RotatingFileHandler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from deployment_history import DeploymentHistory
from service_monitor import ServiceMonitor
from email import encoders
import threading
import requests

# Import deployment history
from deployment_history import deployment_history

# Import service monitor
from service_monitor import initialize_service_monitor

# # # # # # # # # # # # # # # # # #
# # 🔐 Konfigurasi & Inisialisasi #
# # # # # # # # # # # # # # # # # #

@dataclass
class Config:
    TOKEN: str = os.getenv("DEPLOY_TOKEN", "SATindonesia2025")
    LOG_DIR: str = os.getenv("LOG_DIR", "trigger-logs")
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", "7"))
    SERVERS_FILE: str = os.getenv("SERVERS_FILE", "static/servers.json")
    MAX_LOG_SIZE: int = int(os.getenv("MAX_LOG_SIZE", "10485760"))  # 10MB
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Email Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "trigger-deploy@localhost")
    EMAIL_TO: str = os.getenv("EMAIL_TO", "")
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    TELEGRAM_ENABLED: bool = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
    
    # Service Monitoring
    MONITORING_ENABLED: bool = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    MONITORING_INTERVAL: int = int(os.getenv("MONITORING_INTERVAL", "60"))
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "30"))
    ALERT_COOLDOWN: int = int(os.getenv("ALERT_COOLDOWN", "300"))

load_dotenv()

# Setup structured logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

# Add rotating file handler
if not os.path.exists('logs'):
    os.makedirs('logs')

# Initialize config after logger is available
config = Config()

# Log warning if using default token
if config.TOKEN == "SATindonesia2025":
    logger.warning("Using default token. Please set DEPLOY_TOKEN environment variable for production!")

# Enhanced logging setup with multiple handlers
app_handler = RotatingFileHandler('logs/app.log', maxBytes=config.MAX_LOG_SIZE, backupCount=3)
app_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s %(funcName)s:%(lineno)d %(message)s'
))

error_handler = RotatingFileHandler('logs/error.log', maxBytes=config.MAX_LOG_SIZE, backupCount=3)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s %(funcName)s:%(lineno)d %(message)s'
))

security_handler = RotatingFileHandler('logs/security.log', maxBytes=config.MAX_LOG_SIZE, backupCount=3)
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s SECURITY %(funcName)s:%(lineno)d %(message)s'
))

logger.addHandler(app_handler)
logger.addHandler(error_handler)

# Create security logger
security_logger = logging.getLogger('security')
security_logger.addHandler(security_handler)

# Create deployment logger
deployment_logger = logging.getLogger('deployment')
deployment_handler = RotatingFileHandler('logs/deployment.log', maxBytes=config.MAX_LOG_SIZE, backupCount=3)
deployment_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s DEPLOY %(funcName)s:%(lineno)d %(message)s'
))
deployment_logger.addHandler(deployment_handler)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Application start time for metrics
start_time = time.time()

# Rate limiting storage
request_counts = {}

TOKEN = config.TOKEN
LOG_DIR = config.LOG_DIR
SERVERS_FILE = config.SERVERS_FILE
os.makedirs(LOG_DIR, exist_ok=True)

# # # # # # # # # # # # # # # # # #
# # 🧹 clean_old_logs(days=7)    #
# # # # # # # # # # # # # # # # # #
def clean_old_logs(days=7):
    now = datetime.now()
    for filename in os.listdir(LOG_DIR):
        path = os.path.join(LOG_DIR, filename)
        if os.path.isfile(path):
            file_time = datetime.fromtimestamp(os.path.getmtime(path))
            if now - file_time > timedelta(days=days):
                os.remove(path)

# # # # # # # # # # # # # # # # # # #
# # 🔒 Rate Limiting Decorator     #
# # # # # # # # # # # # # # # # # # #
def rate_limit(max_requests=None, window=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            max_req = max_requests or config.RATE_LIMIT_REQUESTS
            win = window or config.RATE_LIMIT_WINDOW
            
            client_ip = request.remote_addr
            now = time.time()
            
            if client_ip not in request_counts:
                request_counts[client_ip] = []
            
            # Clean old requests
            request_counts[client_ip] = [
                req_time for req_time in request_counts[client_ip] 
                if now - req_time < win
            ]
            
            if len(request_counts[client_ip]) >= max_req:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({"error": "Rate limit exceeded"}), 429
            
            request_counts[client_ip].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

# # # # # # # # # # # # # # # # # # #
# # 🔍 Input Validation Functions  #
# # # # # # # # # # # # # # # # # # #
def is_valid_ip(ip):
    """Validate IP address format"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_token(token):
    """Validate authentication token"""
    if not token:
        return False
    return hmac.compare_digest(str(token), str(TOKEN))

# # # # # # # # # # # # # # # # # # # # # # #
# # 📧 Email Notification Functions        #
# # # # # # # # # # # # # # # # # # # # # # #
def send_email_notification(subject, body, log_file=None, is_success=True):
    """Send email notification for deployment events"""
    if not config.EMAIL_ENABLED or not config.EMAIL_TO:
        logger.info("Email notifications disabled or no recipient configured")
        return
    
    def send_async():
        try:
            msg = MIMEMultipart()
            msg['From'] = config.EMAIL_FROM
            msg['To'] = config.EMAIL_TO
            msg['Subject'] = f"[Trigger Deploy] {subject}"
            
            # Add emoji based on success/failure
            emoji = "✅" if is_success else "❌"
            html_body = f"""
            <html>
            <body>
                <h2>{emoji} {subject}</h2>
                <div style="font-family: Arial, sans-serif; margin: 20px;">
                    <p>{body}</p>
                    <hr>
                    <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Server:</strong> Trigger Deploy Platform</p>
                    {f'<p><strong>Log File:</strong> {log_file}</p>' if log_file else ''}
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach log file if provided
            if log_file and os.path.exists(os.path.join(LOG_DIR, log_file)):
                with open(os.path.join(LOG_DIR, log_file), "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {log_file}'
                )
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
            server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(config.EMAIL_FROM, config.EMAIL_TO, text)
            server.quit()
            
            logger.info(f"Email notification sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
    
    # Send email in background thread
    email_thread = threading.Thread(target=send_async)
    email_thread.daemon = True
    email_thread.start()

def notify_deployment_start(server_name, client_ip):
    """Send notification when deployment starts"""
    subject = f"Deployment Started - {server_name}"
    body = f"""
    A new deployment has been triggered.
    
    Server: {server_name}
    Client IP: {client_ip}
    Status: In Progress
    """
    send_email_notification(subject, body, is_success=True)

def notify_deployment_complete(server_name, log_file, success=True):
    """Send notification when deployment completes"""
    status = "Completed Successfully" if success else "Failed"
    subject = f"Deployment {status} - {server_name}"
    body = f"""
    Deployment has {status.lower()}.
    
    Server: {server_name}
    Status: {status}
    Log File: {log_file}
    """
    send_email_notification(subject, body, log_file, success)

def send_telegram_notification(message: str):
    """Send Telegram notification"""
    if not config.TELEGRAM_ENABLED or not config.TELEGRAM_BOT_TOKEN:
        logger.info("Telegram notifications disabled or no token configured")
        return
    
    def send_async():
        try:
            url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram notification sent successfully")
            else:
                logger.error(f"Failed to send Telegram notification: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {str(e)}")
    
    # Send Telegram message in background thread
    telegram_thread = threading.Thread(target=send_async)
    telegram_thread.daemon = True
    telegram_thread.start()

# # # # # # # # # # # # # # # # # # # # # # #
# # 🧪 is_process_running(log_file_path)    #
# # # # # # # # # # # # # # # # # # # # # # #
def is_process_running(log_file_path):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and log_file_path in ' '.join(cmdline):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

# # # # # # # # # # # # # # # # # # # 
# # 🔎 is_valid_server(identifier) #
# # # # # # # # # # # # # # # # # # #
def is_valid_server(identifier, return_details=False):
    try:
        with open(SERVERS_FILE, "r") as f:
            servers = json.load(f)

        for server in servers:
            if server.get("ip") == identifier:
                return server if return_details else True

        return None if return_details else False

    except Exception as e:
        logger.error(f"Error loading servers.json: {e}")
        return None if return_details else False

# # # # # # # # # # # # # # # # # # # # # # #
# # 🚨 Enhanced Error Handlers & Middleware #
# # # # # # # # # # # # # # # # # # # # # # #

class DeploymentError(Exception):
    """Custom exception for deployment-related errors"""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)

@app.errorhandler(Exception)
def handle_exception(e):
    error_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
    logger.error(f"[ERROR-{error_id}] Unhandled exception: {str(e)}", exc_info=True)
    
    if isinstance(e, DeploymentError):
        return jsonify({
            "error": e.message,
            "error_code": e.error_code,
            "error_id": error_id,
            "status": 500
        }), 500
    
    if isinstance(e, ValidationError):
        return jsonify({
            "error": e.message,
            "field": e.field,
            "error_id": error_id,
            "status": 400
        }), 400
    
    return jsonify({
        "error": "Internal server error",
        "error_id": error_id,
        "status": 500
    }), 500

@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 Not Found: {request.url} - IP: {request.remote_addr}")
    return jsonify({
        "error": "Resource not found",
        "status": 404,
        "path": request.path
    }), 404

@app.errorhandler(403)
def forbidden(e):
    security_logger.warning(f"403 Forbidden access attempt: {request.url} - IP: {request.remote_addr}")
    return jsonify({
        "error": "Access forbidden",
        "status": 403
    }), 403

@app.errorhandler(429)
def rate_limit_exceeded(e):
    security_logger.warning(f"Rate limit exceeded: IP: {request.remote_addr}")
    return jsonify({
        "error": "Rate limit exceeded. Please try again later.",
        "status": 429,
        "retry_after": config.RATE_LIMIT_WINDOW
    }), 429

@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path} - IP: {request.remote_addr} - User-Agent: {request.headers.get('User-Agent', 'Unknown')}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code} - {request.method} {request.path}")
    return response

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found", "status": 404}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed", "status": 405}), 405

# # # # # # # # # # # # # # # # # # # # # # #
# # 📊 Enhanced Metrics & Analytics API     #
# # # # # # # # # # # # # # # # # # # # # # #
@app.route('/metrics', methods=['GET'])
def metrics():
    """Basic metrics endpoint for monitoring"""
    try:
        active_deployments = len([
            f for f in os.listdir(LOG_DIR) 
            if is_process_running(os.path.join(LOG_DIR, f))
        ])
        
        return jsonify({
            "status": "healthy",
            "uptime_seconds": time.time() - start_time,
            "active_deployments": active_deployments,
            "total_logs": len(os.listdir(LOG_DIR)),
            "memory_usage_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/metrics/stats', methods=['GET'])
@rate_limit()
def api_metrics_stats():
    """Get deployment statistics"""
    try:
        stats = deployment_history.get_deployment_stats()
        stats["uptime"] = int(time.time() - start_time)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/metrics/history', methods=['GET'])
@rate_limit()
def api_metrics_history():
    """Get deployment history"""
    try:
        limit = int(request.args.get('limit', 20))
        deployments = deployment_history.get_recent_deployments(limit)
        return jsonify({"deployments": deployments})
    except Exception as e:
        logger.error(f"History API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/metrics/servers', methods=['GET'])
@rate_limit()
def api_metrics_servers():
    """Get server statistics"""
    try:
        server_stats = deployment_history.get_server_stats()
        return jsonify({"servers": server_stats})
    except Exception as e:
        logger.error(f"Server stats API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/metrics/system', methods=['GET'])
@rate_limit()
def api_metrics_system():
    """Get system information"""
    try:
        import sys
        import platform
        
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "memory_usage": f"{memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)",
            "disk_usage": f"{disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)",
            "cpu_usage": f"{psutil.cpu_percent(interval=1)}%",
            "uptime": int(time.time() - start_time)
        }
        
        try:
            import flask
            system_info["flask_version"] = flask.__version__
        except:
            system_info["flask_version"] = "Unknown"
        
        return jsonify(system_info)
    except Exception as e:
        logger.error(f"System info API error: {e}")
        return jsonify({"error": str(e)}), 500

# # # # # # # # # # # # # # # # # # # # # # #
# # 🔍 Service Monitoring API               #
# # # # # # # # # # # # # # # # # # # # # # #
@app.route('/services-monitor', methods=['GET'])
def services_monitor_dashboard():
    """Service monitoring dashboard"""
    return render_template("services_monitor.html")

@app.route('/api/services/status', methods=['GET'])
@rate_limit()
def api_services_status():
    """Get current status of all monitored services"""
    try:
        from service_monitor import service_monitor
        if not service_monitor:
            return jsonify({"error": "Service monitor not initialized"}), 500
        
        status = service_monitor.get_service_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Services status API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/services/config', methods=['GET'])
@rate_limit()
def api_services_config():
    """Get services configuration"""
    try:
        with open("static/services.json", 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        logger.error(f"Services config API error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/services/config', methods=['POST'])
@rate_limit(max_requests=3, window=60)
def api_services_config_update():
    """Update services configuration"""
    try:
        # Basic token validation for config updates
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not validate_token(token):
            return jsonify({"error": "Unauthorized"}), 401
        
        new_config = request.get_json()
        
        # Validate config structure
        if not isinstance(new_config, dict):
            return jsonify({"error": "Invalid configuration format"}), 400
        
        # Save configuration
        with open("static/services.json", 'w') as f:
            json.dump(new_config, f, indent=2)
        
        # Reload service monitor
        from service_monitor import service_monitor
        if service_monitor:
            service_monitor.load_services_config()
        
        logger.info("Services configuration updated")
        return jsonify({"status": "success", "message": "Configuration updated"})
        
    except Exception as e:
        logger.error(f"Services config update error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/services/toggle-monitoring', methods=['POST'])
@rate_limit(max_requests=5, window=60)
def api_toggle_monitoring():
    """Toggle service monitoring on/off"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not validate_token(token):
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.get_json() or {}
        enable = data.get('enable', True)
        
        from service_monitor import service_monitor
        if not service_monitor:
            return jsonify({"error": "Service monitor not initialized"}), 500
        
        if enable:
            service_monitor.start_monitoring()
            message = "Service monitoring started"
        else:
            service_monitor.stop_monitoring()
            message = "Service monitoring stopped"
        
        logger.info(message)
        return jsonify({"status": "success", "message": message, "monitoring_active": enable})
        
    except Exception as e:
        logger.error(f"Toggle monitoring error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return render_template("home.html")

@app.route("/metrics-dashboard")
def metrics_dashboard():
    return render_template("metrics.html")

@app.route("/deploy-servers")
def deploy_servers():
    return render_template("deploy_servers.html")

@app.route("/invalid-token")
def invalid_token():
    return render_template("invalid_token.html")

@app.route("/trigger-result")
def trigger_result():
    log_file = request.args.get("log", "No log file specified")
    message = request.args.get("message", "Deployment completed")
    return render_template("trigger_result.html", log_file=log_file, message=message)


@app.route('/servers', methods=['GET'])
@rate_limit()
def get_servers():
    try:
        with open(SERVERS_FILE, "r") as f:
            servers = json.load(f)
        return jsonify(servers)
    except Exception as e:
        logger.error(f"Failed to load servers.json: {e}")
        return jsonify({"error": f"Failed to load servers.json: {str(e)}"}), 500


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/trigger', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=60)
def trigger_deploy():
    deployment_id = None
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            token = data.get("token")
            server = data.get("server")
        else:
            token = request.args.get("token")
            server = request.args.get("server")

        # Enhanced token validation
        if not validate_token(token):
            security_logger.warning(f"Invalid token attempt from IP: {request.remote_addr}")
            return jsonify({"error": "Invalid token", "status": 403}), 403

        # Get server details
        server_details = is_valid_server(server, return_details=True) if server else None
        server_name = server_details.get("name", "Default Server") if server_details else "Default Server"
        server_ip = server or "default"

        # Input validation
        if server is not None:
            server = server.strip()
            if server == "":
                server = None
            elif not is_valid_ip(server):
                logger.warning(f"Invalid IP format: {server}")
                raise ValidationError("Invalid server IP format", "server")
            elif not server_details:
                logger.warning(f"Server not found in configuration: {server}")
                raise ValidationError("Invalid server IP or alias", "server")

        clean_old_logs(config.LOG_RETENTION_DAYS)

        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        log_filename = f"trigger-{timestamp}.log"
        log_path = os.path.join(LOG_DIR, log_filename)

        # Add to deployment history
        deployment_id = deployment_history.add_deployment(
            server_name=server_name,
            server_ip=server_ip,
            client_ip=request.remote_addr,
            log_file=log_filename,
            status="started"
        )

        # Log deployment start
        with open(log_path, "a") as log:
            log.write(f"[{datetime.now()}] 🚀 Deploy trigger received. Server: {server_name} ({server_ip})\n")
            log.write(f"[{datetime.now()}] 📋 Client IP: {request.remote_addr}\n")
            log.write(f"[{datetime.now()}] 🆔 Deployment ID: {deployment_id}\n")

        deployment_logger.info(f"Deploy triggered for server: {server_name} by IP: {request.remote_addr} - ID: {deployment_id}")

        # Send start notification
        notify_deployment_start(server_name, request.remote_addr)

        with open(log_path, "a") as log:
            log.write(f"[{datetime.now()}] ✅ Spawning deploy-wrapper.sh process...\n")

        # Start deployment process
        if server:
            process = subprocess.Popen(["./deploy-wrapper.sh", log_path, server],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        else:
            process = subprocess.Popen(["./deploy-wrapper.sh", log_path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

        with open(log_path, "a") as log:
            log.write(f"[{datetime.now()}] 🔄 Process started (PID: {process.pid}), streaming from log file: {log_filename}\n")

        # Schedule completion check (async)
        def check_completion():
            try:
                time.sleep(5)  # Wait a bit for process to start
                process.wait()  # Wait for completion
                
                success = process.returncode == 0
                status = "completed" if success else "failed"
                
                deployment_history.update_deployment(deployment_id, status, success)
                notify_deployment_complete(server_name, log_filename, success)
                
                deployment_logger.info(f"Deployment {deployment_id} {status} with return code: {process.returncode}")
                
            except Exception as e:
                logger.error(f"Error in completion check for {deployment_id}: {e}")
                deployment_history.update_deployment(deployment_id, "failed", False)
                notify_deployment_complete(server_name, log_filename, False)
        
        completion_thread = threading.Thread(target=check_completion)
        completion_thread.daemon = True
        completion_thread.start()

        view_url = url_for('get_log_file', filename=log_filename, _external=True).replace("http://", "https://")
        stream_url = url_for('stream_log', file=log_filename, _external=True).replace("http://", "https://")

        return jsonify({
            "status": "success",
            "deployment_id": deployment_id,
            "log_file": log_filename,
            "view_log_url": view_url,
            "stream_log_url": stream_url,
            "timestamp": datetime.now().isoformat(),
            "server_name": server_name
        }), 200
        
    except ValidationError as e:
        if deployment_id:
            deployment_history.update_deployment(deployment_id, "failed", False)
        raise e
    except Exception as e:
        if deployment_id:
            deployment_history.update_deployment(deployment_id, "failed", False)
        deployment_logger.error(f"Deploy trigger error: {str(e)}", exc_info=True)
        if 'log_path' in locals():
            with open(log_path, "a") as log:
                log.write(f"[{datetime.now()}] ❌ Deploy error: {str(e)}\n")
        raise DeploymentError(f"Deployment failed: {str(e)}", "DEPLOY_ERROR")

@app.route("/ping", methods=["GET", "POST"])
@rate_limit(max_requests=20, window=60)
def ping_server():
    logger.info(f"Ping request from IP: {request.remote_addr}")
    
    # Only allow POST requests
    if request.method == "GET":
        return jsonify({
            "status": "error",
            "message": "This endpoint only supports POST with JSON payload"
        }), 405

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Missing JSON payload"}), 400
            
        server_id = data.get("server")
        if not server_id:
            return jsonify({"status": "error", "message": "Missing server IP"}), 400

        # Validate IP format
        if not is_valid_ip(server_id):
            logger.warning(f"Invalid IP format in ping request: {server_id}")
            return jsonify({"status": "error", "message": "Invalid IP format"}), 400

        # Load and validate server configuration
        try:
            with open(SERVERS_FILE) as f:
                servers = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load servers.json: {e}")
            return jsonify({"status": "error", "message": f"Failed to load servers.json: {str(e)}"}), 500

        match = next((s for s in servers if s["ip"] == server_id), None)
        if not match:
            logger.warning(f"Server IP not found in configuration: {server_id}")
            return jsonify({"status": "error", "message": f"Server IP '{server_id}' not found"}), 404

        ip = match["ip"]
        user = match.get("user")
        if not user:
            logger.error(f"Missing user configuration for server: {server_id}")
            return jsonify({"status": "error", "message": "Missing user in servers.json"}), 400

        # Perform SSH ping
        try:
            subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", 
                 "-o", "ConnectTimeout=5", f"{user}@{ip}", "exit"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            logger.info(f"SSH ping successful to {user}@{ip}")
            return jsonify({"status": "ok", "server": server_id, "timestamp": datetime.now().isoformat()})
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"SSH ping failed to {user}@{ip}: {e}")
            return jsonify({"status": "unreachable", "server": server_id}), 503
        except subprocess.TimeoutExpired:
            logger.warning(f"SSH ping timeout to {user}@{ip}")
            return jsonify({"status": "timeout", "server": server_id}), 503
            
    except Exception as e:
        logger.error(f"Ping server error: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/logs', methods=['GET'])
@rate_limit()
def list_logs():
    try:
        logs = sorted(os.listdir(LOG_DIR), reverse=True)
        return jsonify(logs)
    except Exception as e:
        logger.error(f"Failed to list logs: {e}")
        return jsonify({"error": "Failed to list logs"}), 500


@app.route('/log-content', methods=['GET'])
@rate_limit()
def log_content():
    filename = request.args.get("file")
    if not filename:
        return jsonify({"error": "Missing file parameter"}), 400
    
    # Security: validate filename
    if not filename.endswith('.log') or '/' in filename or '..' in filename:
        logger.warning(f"Invalid log file request: {filename}")
        return jsonify({"error": "Invalid file name"}), 400
        
    path = os.path.join(LOG_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
        
    try:
        with open(path, "r") as f:
            content = f.read()
        return jsonify({"content": content, "filename": filename})
    except Exception as e:
        logger.error(f"Failed to read log file {filename}: {e}")
        return jsonify({"error": "Failed to read file"}), 500


@app.route('/stream-log', methods=['GET'])
@rate_limit()
def stream_log():
    filename = request.args.get("file")
    if not filename:
        return jsonify({"error": "No log file specified"}), 400

    # Security: validate filename
    if not filename.endswith('.log') or '/' in filename or '..' in filename:
        logger.warning(f"Invalid log file stream request: {filename}")
        return jsonify({"error": "Invalid file name"}), 400

    full_path = os.path.join(LOG_DIR, filename)
    if not os.path.isfile(full_path):
        return jsonify({"error": "Log file not found"}), 404

    def generate():
        try:
            with open(full_path, 'r') as f:
                f.seek(0)  # Start from beginning
                while True:
                    line = f.readline()
                    if not line:
                        # Check if deployment process is still running
                        if not is_process_running(full_path):
                            yield "data: ✅ Deploy complete.\n\n"
                            break
                        time.sleep(1)
                        continue
                    yield f"data: {line.strip()}\n\n"
        except Exception as e:
            logger.error(f"Error streaming log {filename}: {e}")
            yield f"data: ❌ Error reading log: {str(e)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/logs/<path:filename>', methods=['GET'])
@rate_limit()
def get_log_file(filename):
    # Security: validate filename
    if not filename.endswith('.log') or '/' in filename or '..' in filename:
        logger.warning(f"Invalid log file download request: {filename}")
        return jsonify({"error": "Invalid file name"}), 403
        
    try:
        return send_from_directory(LOG_DIR, filename)
    except Exception as e:
        logger.error(f"Failed to serve log file {filename}: {e}")
        return jsonify({"error": "File not found"}), 404


@app.route('/health', methods=['GET'])
@rate_limit(max_requests=30, window=60)
def health():
    target = request.args.get("target") or "google.co.id"
    result = {"target": target, "resolve": None, "ping": None, "timestamp": datetime.now().isoformat()}

    try:
        ip = socket.gethostbyname(target)
        result["resolve"] = f"{target} resolved to {ip}"
        logger.info(f"DNS resolution successful for {target} -> {ip}")
    except Exception as e:
        result["resolve"] = f"❌ DNS resolve failed: {str(e)}"
        logger.warning(f"DNS resolution failed for {target}: {e}")

    try:
        param = '-n' if os.name == 'nt' else '-c'
        ping_cmd = ["ping", param, "3", target]
        ping_result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=10)
        
        if ping_result.returncode == 0:
            result["ping"] = "✅ Ping successful"
            logger.info(f"Ping successful to {target}")
        else:
            result["ping"] = f"❌ Ping failed: {ping_result.stderr}"
            logger.warning(f"Ping failed to {target}: {ping_result.stderr}")
            
    except subprocess.TimeoutExpired:
        result["ping"] = "❌ Ping timeout"
        logger.warning(f"Ping timeout to {target}")
    except Exception as e:
        result["ping"] = f"❌ Ping error: {str(e)}"
        logger.error(f"Ping error to {target}: {e}")

    return jsonify(result)

# # # # # # # # # # # # # # # # # # # # # # #
# # 🚀 Application Startup                  #
# # # # # # # # # # # # # # # # # # # # # # #

# Global instances
deployment_history = None
service_monitor = None

def initialize_components():
    """Initialize global components"""
    global deployment_history, service_monitor
    
    try:
        # Initialize deployment history
        deployment_history = DeploymentHistory()
        logger.info("✅ Deployment history initialized")
        
        # Initialize service monitor
        service_monitor = ServiceMonitor()
        logger.info("✅ Service monitor initialized")
        
        # Start monitoring in background
        service_monitor.start_monitoring()
        logger.info("✅ Service monitoring started")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}")
        raise

if __name__ == '__main__':
    logger.info("=== Starting Trigger Deploy Server ===")
    logger.info(f"Configuration: LOG_DIR={LOG_DIR}, SERVERS_FILE={SERVERS_FILE}")
    logger.info(f"Rate limiting: {config.RATE_LIMIT_REQUESTS} requests per {config.RATE_LIMIT_WINDOW}s")
    
    # Ensure directories exist
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Clean old logs on startup
    try:
        clean_old_logs(config.LOG_RETENTION_DAYS)
        logger.info(f"Cleaned logs older than {config.LOG_RETENTION_DAYS} days")
    except Exception as e:
        logger.warning(f"Failed to clean old logs: {e}")
    
    # Validate servers.json exists
    if not os.path.exists(SERVERS_FILE):
        logger.warning(f"Servers file not found: {SERVERS_FILE}")
    
    # Initialize components
    initialize_components()
    
    logger.info("Server ready to accept connections")
    app.run(host='0.0.0.0', port=5000, debug=False)
