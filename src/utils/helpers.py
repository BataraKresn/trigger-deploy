# =================================
# Utility Functions
# =================================

import os
import hmac
import json
import subprocess
import socket
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from src.models.config import config
from src.models.entities import Server, Service, Deployment


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_token(token: str) -> bool:
    """Validate authentication token"""
    if not token:
        return False
    return hmac.compare_digest(str(token), str(config.TOKEN))


def check_server_health(ip: str, port: int = 22, timeout: int = 3) -> str:
    """Check if server is reachable via ping and port check"""
    try:
        # Check ping first (quick check)
        ping_result = subprocess.run(
            ['ping', '-c', '1', '-W', '2', ip], 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        if ping_result.returncode != 0:
            return 'offline'
        
        # Check if SSH port is open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            return 'online'
        else:
            return 'unknown'  # Ping works but SSH port closed
            
    except (subprocess.TimeoutExpired, OSError, Exception) as e:
        logger.debug(f"Health check failed for {ip}: {e}")
        return 'offline'


def load_servers() -> List[Server]:
    """Load servers from configuration file"""
    try:
        with open(config.SERVERS_FILE, 'r') as f:
            servers_data = json.load(f)
        
        servers = []
        for server_data in servers_data:
            server = Server.from_dict(server_data)
            server.status = check_server_health(server.ip, server.port)
            servers.append(server)
        
        return servers
    except Exception as e:
        logger.error(f"Failed to load servers: {e}")
        return []


def load_services() -> List[Service]:
    """Load services from configuration file"""
    try:
        with open(config.SERVICES_FILE, 'r') as f:
            services_data = json.load(f)
        
        return [Service.from_dict(service_data) for service_data in services_data]
    except Exception as e:
        logger.error(f"Failed to load services: {e}")
        return []


def is_valid_server(server_ip: str, return_details: bool = False) -> bool | Dict[str, Any]:
    """Check if server IP is valid and optionally return server details"""
    servers = load_servers()
    
    for server in servers:
        if server.ip == server_ip or server.alias == server_ip:
            if return_details:
                return server.to_dict()
            return True
    
    return False if not return_details else {}


def generate_deployment_id() -> str:
    """Generate unique deployment ID"""
    from datetime import datetime
    return f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def format_uptime(seconds: float) -> str:
    """Format uptime in human readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days}d {hours}h"


def cleanup_old_logs() -> None:
    """Remove old log files based on retention policy"""
    if not os.path.exists(config.LOG_DIR):
        return
    
    cutoff_date = datetime.now() - timedelta(days=config.LOG_RETENTION_DAYS)
    
    for filename in os.listdir(config.LOG_DIR):
        file_path = os.path.join(config.LOG_DIR, filename)
        if os.path.isfile(file_path):
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mtime < cutoff_date:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed old log file: {filename}")
                except Exception as e:
                    logger.error(f"Failed to remove old log file {filename}: {e}")


def send_email_notification(subject: str, body: str, log_file: Optional[str] = None, is_success: bool = True) -> None:
    """Send email notification for deployment events"""
    if not config.EMAIL_ENABLED or not config.EMAIL_TO:
        logger.info("Email notifications disabled or no recipient configured")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config.SMTP_USERNAME
        msg['To'] = config.EMAIL_TO
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add log file as attachment if provided
        if log_file and os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_content = f.read()
            msg.attach(MIMEText(log_content, 'plain', 'utf-8'))
        
        # Send email
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email notification sent successfully to {config.EMAIL_TO}")
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")


def ping_check(target: str) -> Dict[str, Any]:
    """Perform ping check on target"""
    import subprocess
    try:
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '3', target],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        success = result.returncode == 0
        return {
            'success': success,
            'message': '✅ Ping successful' if success else '❌ Ping failed',
            'details': result.stdout if success else result.stderr
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'❌ Ping error: {str(e)}',
            'details': ''
        }


def dns_resolve_check(target: str) -> Dict[str, Any]:
    """Perform DNS resolution check"""
    import socket
    try:
        ip = socket.gethostbyname(target)
        return {
            'success': True,
            'message': f'✅ DNS resolved to {ip}',
            'ip': ip
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'❌ DNS resolve failed: {str(e)}',
            'ip': None
        }


def http_check(target: str) -> Dict[str, Any]:
    """Perform HTTP check on target"""
    import requests
    try:
        # Add protocol if not present
        if not target.startswith(('http://', 'https://')):
            target = f'http://{target}'
        
        response = requests.get(target, timeout=10)
        return {
            'success': response.status_code == 200,
            'message': f'✅ HTTP {response.status_code}' if response.status_code == 200 else f'❌ HTTP {response.status_code}',
            'status_code': response.status_code,
            'response_time': response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'❌ HTTP error: {str(e)}',
            'status_code': None,
            'response_time': None
        }
