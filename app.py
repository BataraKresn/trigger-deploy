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

# # # # # # # # # # # # # # # # # #
# # 🔐 Konfigurasi & Inisialisasi #
# # # # # # # # # # # # # # # # # #

@dataclass
class Config:
    TOKEN: str = os.getenv("DEPLOY_TOKEN", "SATindonesia2025")  # Fallback for backward compatibility
    LOG_DIR: str = os.getenv("LOG_DIR", "trigger-logs")
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", "7"))
    SERVERS_FILE: str = os.getenv("SERVERS_FILE", "static/servers.json")
    MAX_LOG_SIZE: int = int(os.getenv("MAX_LOG_SIZE", "10485760"))  # 10MB
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

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

handler = RotatingFileHandler('logs/app.log', maxBytes=config.MAX_LOG_SIZE, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s'
))
logger.addHandler(handler)

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
# # 🚨 Global Error Handlers & Middleware  #
# # # # # # # # # # # # # # # # # # # # # # #
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "status": 500
    }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found", "status": 404}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed", "status": 405}), 405

# # # # # # # # # # # # # # # # # # # # # # #
# # 📊 Health & Metrics Endpoints           #
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

@app.route('/')
def home():
    return render_template("home.html")


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
            logger.warning(f"Invalid token attempt from IP: {request.remote_addr}")
            return jsonify({"error": "Invalid token", "status": 403}), 403

        # Input validation
        if server is not None:
            server = server.strip()
            if server == "":
                server = None
            elif not is_valid_ip(server):
                logger.warning(f"Invalid IP format: {server}")
                return jsonify({"error": "Invalid server IP format", "status": 400}), 400
            elif not is_valid_server(server):
                logger.warning(f"Server not found in configuration: {server}")
                return jsonify({"error": "Invalid server IP or alias", "status": 400}), 400

        clean_old_logs(config.LOG_RETENTION_DAYS)

        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        log_filename = f"trigger-{timestamp}.log"
        log_path = os.path.join(LOG_DIR, log_filename)

        # Log deployment start
        with open(log_path, "a") as log:
            log.write(f"[{datetime.now()}] 🚀 Deploy trigger received. Server: {server or 'default'}\n")
            log.write(f"[{datetime.now()}] 📋 Client IP: {request.remote_addr}\n")

        logger.info(f"Deploy triggered for server: {server or 'default'} by IP: {request.remote_addr}")

        with open(log_path, "a") as log:
            log.write(f"[{datetime.now()}] ✅ Spawning deploy-wrapper.sh process...\n")

        if server:
            subprocess.Popen(["./deploy-wrapper.sh", log_path, server],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        else:
            subprocess.Popen(["./deploy-wrapper.sh", log_path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

        with open(log_path, "a") as log:
            log.write(f"[{datetime.now()}] 🔄 Process started, streaming from log file: {log_filename}\n")

        view_url = url_for('get_log_file', filename=log_filename, _external=True).replace("http://", "https://")
        stream_url = url_for('stream_log', file=log_filename, _external=True).replace("http://", "https://")

        return jsonify({
            "status": "success",
            "log_file": log_filename,
            "view_log_url": view_url,
            "stream_log_url": stream_url,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Deploy trigger error: {str(e)}", exc_info=True)
        if 'log_path' in locals():
            with open(log_path, "a") as log:
                log.write(f"[{datetime.now()}] ❌ Deploy error: {str(e)}\n")
        return jsonify({"status": "error", "message": str(e)}), 500

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
    
    logger.info("Server ready to accept connections")
    app.run(host='0.0.0.0', port=5000, debug=False)
