# =================================
# API Routes
# =================================

from flask import Blueprint, jsonify, request
from datetime import datetime
from src.utils.helpers import (
    load_servers, load_services, ping_check, 
    dns_resolve_check, http_check
)
from src.models.entities import Server, Service


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
        # Mock deployment history
        deployments = [
            {
                'deployment_id': 'deploy-20250720-100426',
                'server_name': 'Default Server',
                'server_ip': 'default',
                'started_at': '2025-07-20T10:04:26',
                'completed_at': '2025-07-20T10:04:31',
                'status': 'success',
                'duration': 5.0,
                'client_ip': '172.68.82.148',
                'log_file': 'trigger-20250720-100426.log'
            },
            {
                'deployment_id': 'deploy-20250720-100122',
                'server_name': 'Default Server',
                'server_ip': 'default',
                'started_at': '2025-07-20T10:01:22',
                'completed_at': None,
                'status': 'failed',
                'duration': None,
                'client_ip': '172.68.82.148',
                'log_file': 'trigger-20250720-100122.log'
            },
            {
                'deployment_id': 'deploy-20250720-095238',
                'server_name': 'Default Server',
                'server_ip': 'default',
                'started_at': '2025-07-20T09:52:38',
                'completed_at': None,
                'status': 'failed',
                'duration': None,
                'client_ip': '172.71.82.40',
                'log_file': 'trigger-20250720-095238.log'
            }
        ]
        
        return jsonify({'deployments': deployments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
