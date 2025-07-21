# =================================
# API Routes
# =================================

from flask import Blueprint, jsonify, request
from datetime import datetime
import json
import os
from src.utils.helpers import (
    load_servers, load_services, ping_check, 
    dns_resolve_check, http_check
)
from src.models.entities import Server, Service
from src.models.config import config
from src.utils.deployment_history import deployment_history
from src.utils.service_monitor import service_monitor


api_bp = Blueprint('api', __name__, url_prefix='/api')


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
