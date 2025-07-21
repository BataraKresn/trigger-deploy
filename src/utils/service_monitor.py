# =================================
# Service Monitor Integration
# =================================

import docker
import requests
import json
import time
import threading
import subprocess
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import os
from src.models.config import config

logger = logging.getLogger('service_monitor')


class ServiceMonitor:
    """Enhanced service monitor with Docker and HTTP service monitoring"""
    
    def __init__(self):
        self.services = self.load_services()
        self.docker_client = None
        self.monitoring_active = False
        self.init_docker_client()
    
    def init_docker_client(self):
        """Initialize Docker client if available"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")
            self.docker_client = None
    
    def load_services(self) -> List[Dict]:
        """Load services from configuration"""
        try:
            with open(config.SERVICES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load services: {e}")
            return []
    
    def check_docker_service(self, service_name: str) -> Dict:
        """Check Docker container status"""
        if not self.docker_client:
            return {
                'status': 'unknown',
                'message': 'Docker client not available'
            }
        
        try:
            container = self.docker_client.containers.get(service_name)
            status = container.status
            
            # Get container creation time for uptime calculation
            created = container.attrs['Created']
            created_time = datetime.fromisoformat(created.replace('Z', '+00:00').replace('.', ''))
            uptime = datetime.now() - created_time.replace(tzinfo=None)
            
            return {
                'status': 'online' if status == 'running' else 'offline',
                'container_status': status,
                'uptime': self._format_uptime(uptime.total_seconds()),
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'ports': self._format_ports(container.ports),
                'message': f'Container {status}'
            }
        except docker.errors.NotFound:
            return {
                'status': 'offline',
                'message': 'Container not found'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking container: {str(e)}'
            }
    
    def check_http_service(self, url: str, timeout: int = 10) -> Dict:
        """Check HTTP service status"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            response_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'online' if response.status_code == 200 else 'warning',
                'status_code': response.status_code,
                'response_time': f"{response_time:.2f}ms",
                'message': f'HTTP {response.status_code}'
            }
        except requests.exceptions.Timeout:
            return {
                'status': 'warning',
                'message': 'Request timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'offline',
                'message': 'Connection failed'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'HTTP error: {str(e)}'
            }
    
    def check_all_services(self) -> List[Dict]:
        """Check status of all configured services"""
        results = []
        
        for service in self.services:
            service_result = {
                'name': service['name'],
                'type': service.get('type', 'http'),
                'last_check': datetime.now().isoformat()
            }
            
            if service.get('type') == 'docker':
                status = self.check_docker_service(service['name'])
            else:
                status = self.check_http_service(service['url'])
            
            service_result.update(status)
            results.append(service_result)
        
        return results
    
    def _format_uptime(self, seconds: float) -> str:
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
    
    def _format_ports(self, ports: Dict) -> str:
        """Format container ports for display"""
        if not ports:
            return "No exposed ports"
        
        port_list = []
        for container_port, host_bindings in ports.items():
            if host_bindings:
                for binding in host_bindings:
                    host_port = binding['HostPort']
                    port_list.append(f"{host_port}:{container_port}")
            else:
                port_list.append(container_port)
        
        return ", ".join(port_list)

    def check_all_local_services(self) -> List[Dict]:
        """Check all local Docker services"""
        local_services = []
        if self.docker_client:
            try:
                containers = self.docker_client.containers.list(all=True)
                for container in containers:
                    service_info = self.check_docker_service(container.name)
                    if service_info.get('found'):
                        local_services.append(service_info)
            except Exception as e:
                logger.error(f"Error checking local services: {e}")
        return local_services

    def check_all_remote_services(self) -> List[Dict]:
        """Check all remote HTTP services"""
        remote_services = []
        for service in self.services:
            if service.get('type') == 'http' or 'url' in service:
                status = self.check_http_service(service.get('url', ''))
                status['name'] = service.get('name', 'Unknown')
                status['description'] = service.get('description', '')
                status['critical'] = service.get('critical', False)
                remote_services.append(status)
        return remote_services

    def get_services_summary(self) -> Dict:
        """Get summary of all services"""
        local = self.check_all_local_services()
        remote = self.check_all_remote_services()
        
        total_services = len(local) + len(remote)
        healthy_count = sum(1 for s in local + remote if s.get('status') == 'healthy')
        unhealthy_count = total_services - healthy_count
        critical_down = sum(1 for s in local + remote 
                          if s.get('critical', False) and s.get('status') != 'healthy')
        
        return {
            'total_services': total_services,
            'healthy_services': healthy_count,
            'unhealthy_services': unhealthy_count,
            'critical_down': critical_down,
            'local_services_count': len(local),
            'remote_services_count': len(remote)
        }


# Global service monitor instance
service_monitor = ServiceMonitor()
