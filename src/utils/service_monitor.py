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
            # Check if Docker monitoring is enabled via environment
            docker_enabled = os.getenv('DOCKER_ENABLED', 'true').lower() == 'true'
            if not docker_enabled:
                logger.info("Docker monitoring is disabled via DOCKER_ENABLED=false")
                self.docker_client = None
                return
                
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")
            logger.info("Service monitoring will work without Docker integration")
            self.docker_client = None
    
    def load_services(self) -> List[Dict]:
        """Load services from configuration"""
        try:
            if not os.path.exists(config.SERVICES_FILE):
                logger.warning(f"Services file not found: {config.SERVICES_FILE}")
                return []
                
            with open(config.SERVICES_FILE, 'r') as f:
                data = json.load(f)
                
            # Handle both old format (list) and new format (dict with local/remote)
            if isinstance(data, list):
                logger.info("Converting old services format to new format")
                return data
            elif isinstance(data, dict):
                # Combine local and remote services
                services = []
                if 'local_services' in data:
                    services.extend(data['local_services'])
                if 'remote_services' in data:
                    services.extend(data['remote_services'])
                return services
            else:
                logger.error("Invalid services file format")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in services file: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to load services: {e}")
            return []
    
    def check_docker_service(self, service_name: str) -> Dict:
        """Check Docker container status"""
        if self.docker_client is None:
            return {
                'name': service_name,
                'status': 'unavailable',
                'message': 'Docker client not available',
                'timestamp': datetime.now().isoformat()
            }
            
        try:
            container = self.docker_client.containers.get(service_name)
            return {
                'name': service_name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'created': container.attrs['Created'],
                'timestamp': datetime.now().isoformat()
            }
        except docker.errors.NotFound:
            return {
                'name': service_name,
                'status': 'not_found',
                'message': f'Container {service_name} not found',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking Docker service {service_name}: {e}")
            return {
                'name': service_name,
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
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
        
        # First check services from config file
        for service in self.services:
            if service.get('type') == 'docker' and service.get('container_name'):
                service_info = self.check_docker_service(service.get('container_name'))
                service_info['name'] = service.get('name', service.get('container_name'))
                service_info['description'] = service.get('description', '')
                service_info['critical'] = service.get('critical', False)
                service_info['port'] = service.get('port')
                local_services.append(service_info)
        
        # Then check all running Docker containers if client is available
        if self.docker_client:
            try:
                containers = self.docker_client.containers.list(all=True)
                existing_names = [s.get('name') for s in local_services]
                
                for container in containers:
                    if container.name not in existing_names:
                        service_info = self.check_docker_service(container.name)
                        if service_info.get('status') != 'error':
                            local_services.append(service_info)
            except Exception as e:
                logger.error(f"Error checking local services: {e}")
        
        return local_services

    def check_all_remote_services(self) -> List[Dict]:
        """Check all remote HTTP services"""
        remote_services = []
        for service in self.services:
            if service.get('type') == 'http' or 'url' in service:
                try:
                    status = self.check_http_service(service.get('url', ''))
                    status['name'] = service.get('name', 'Unknown')
                    status['description'] = service.get('description', '')
                    status['critical'] = service.get('critical', False)
                    remote_services.append(status)
                except Exception as e:
                    logger.error(f"Error checking remote service {service.get('name')}: {e}")
                    remote_services.append({
                        'name': service.get('name', 'Unknown'),
                        'status': 'error',
                        'message': str(e),
                        'description': service.get('description', ''),
                        'critical': service.get('critical', False),
                        'timestamp': datetime.now().isoformat()
                    })
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
