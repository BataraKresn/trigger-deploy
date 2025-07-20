# =================================
# Deployment Routes
# =================================

from flask import Blueprint, request, jsonify
import subprocess
import os
import time
from datetime import datetime
from src.utils.helpers import (
    validate_token, is_valid_server, generate_deployment_id,
    send_email_notification, cleanup_old_logs
)
from src.models.config import config


deploy_bp = Blueprint('deploy', __name__)


@deploy_bp.route('/trigger', methods=['GET', 'POST'])
def trigger_deploy():
    """Trigger deployment"""
    deployment_id = None
    
    try:
        # Extract data from request
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            token = data.get("token")
            server = data.get("server")
        else:
            token = request.args.get("token")
            server = request.args.get("server")

        # Validate token
        if not validate_token(token):
            return jsonify({"error": "Invalid token", "status": 403}), 403

        # Get server details
        server_details = is_valid_server(server, return_details=True) if server else None
        server_name = server_details.get("name", "Default Server") if server_details else "Default Server"
        server_ip = server or "default"

        # Generate deployment ID
        deployment_id = generate_deployment_id()
        
        # Prepare log file
        log_file = f"trigger-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
        log_path = os.path.join(config.LOG_DIR, log_file)

        # Create log directory if it doesn't exist
        os.makedirs(config.LOG_DIR, exist_ok=True)

        # Start deployment process
        deploy_command = ["bash", os.path.join("scripts", "deploy-wrapper.sh")]
        
        # Add server parameter if provided
        if server:
            deploy_command.extend([server])

        # Execute deployment
        with open(log_path, "w") as log:
            log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Deploy trigger received. Server: {server_name} ({server_ip})\n")
            log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📋 Client IP: {request.remote_addr}\n")
            log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🆔 Deployment ID: {deployment_id}\n")
            log.flush()

            process = subprocess.Popen(
                deploy_command,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

        # Cleanup old logs
        cleanup_old_logs()

        # Send success response
        response_data = {
            "message": "Deployment triggered successfully",
            "deployment_id": deployment_id,
            "server": server_name,
            "log_file": log_file,
            "status": "started",
            "timestamp": datetime.now().isoformat()
        }

        # Send email notification if enabled
        if config.EMAIL_ENABLED:
            subject = f"Deployment Started: {server_name}"
            body = f"""
Deployment has been triggered successfully.

Details:
- Server: {server_name} ({server_ip})
- Deployment ID: {deployment_id}
- Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Client IP: {request.remote_addr}
- Log file: {log_file}

You can monitor the progress in the dashboard.
            """
            send_email_notification(subject, body, log_path)

        return jsonify(response_data)

    except subprocess.CalledProcessError as e:
        error_msg = f"Deployment script failed: {e}"
        if deployment_id:
            log_path = os.path.join(config.LOG_DIR, f"trigger-{deployment_id}.log")
            if os.path.exists(log_path):
                with open(log_path, "a") as log:
                    log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Error: {error_msg}\n")
        
        return jsonify({"error": error_msg, "status": 500}), 500

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        if deployment_id:
            log_path = os.path.join(config.LOG_DIR, f"trigger-{deployment_id}.log")
            if os.path.exists(log_path):
                with open(log_path, "a") as log:
                    log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Error: {error_msg}\n")
        
        return jsonify({"error": error_msg, "status": 500}), 500
