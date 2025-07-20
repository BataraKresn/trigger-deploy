# =================================
# Service Monitor - Docker & Remote Services
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

logger = logging.getLogger('service_monitor')

class ServiceMonitor:
    def __init__(self, config):
        self.config = config
        self.services = {}
        self.service_states = {}
        self.alert_history = {}
        self.monitoring_active = False
        self.docker_client = None
        
        # Initialize Docker client
        self.init_docker_client()
        
        # Load services configuration
        self.load_services_config()
        
    def init_docker_client(self):
        """Initialize Docker client"""
        try:
            # Test Docker connection
            self.docker_client = docker.from_env()
            # Test if we can actually connect by listing containers
            self.docker_client.containers.list(limit=1)
            logger.info("Docker client initialized successfully")
        except docker.errors.DockerException as e:
            logger.error(f"Docker API error: {e}")
            self.docker_client = None
        except Exception as e:
            logger.error(f"Docker client initialization failed: {e}")
            self.docker_client = None
    
    def load_services_config(self):
        """Load services configuration from file"""
        config_file = "static/services.json"
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.services = json.load(f)
                logger.info(f"Loaded {len(self.services)} services for monitoring")
            else:
                # Create default config
                self.create_default_services_config(config_file)
        except Exception as e:
            logger.error(f"Error loading services config: {e}")
            self.services = {}
    
    def create_default_services_config(self, config_file):
        """Create default services configuration"""
        default_services = {
            "local_services": [
                {
                    "name": "Nginx",
                    "type": "docker",
                    "container_name": "nginx",
                    "port": 80,
                    "health_endpoint": "http://localhost",
                    "critical": True
                },
                {
                    "name": "Database",
                    "type": "docker", 
                    "container_name": "postgres",
                    "port": 5432,
                    "critical": True
                }
            ],
            "remote_services": [
                {
                    "name": "Production API",
                    "type": "http",
                    "url": "https://api.yourdomain.com/health",
                    "expected_status": 200,
                    "timeout": 10,
                    "critical": True
                },
                {
                    "name": "Remote Database",
                    "type": "tcp",
                    "host": "db.yourdomain.com",
                    "port": 5432,
                    "timeout": 5,
                    "critical": False
                }
            ]
        }
        
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_services, f, indent=2)
        
        self.services = default_services
        logger.info("Created default services configuration")
    
    def start_monitoring(self):
        """Start service monitoring in background thread"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitor_thread.start()
        logger.info("Service monitoring started")
    
    def stop_monitoring(self):
        """Stop service monitoring"""
        self.monitoring_active = False
        logger.info("Service monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self.check_all_services()
                time.sleep(int(self.config.get('MONITORING_INTERVAL', 60)))
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)
    
    def check_all_services(self):
        """Check all configured services"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "local_services": [],
            "remote_services": [],
            "summary": {
                "total": 0,
                "healthy": 0,
                "unhealthy": 0,
                "critical_down": 0
            }
        }
        
        # Check local services (Docker containers)
        if "local_services" in self.services:
            for service in self.services["local_services"]:
                result = self.check_local_service(service)
                results["local_services"].append(result)
                self._update_summary(results["summary"], result)
        
        # Check remote services
        if "remote_services" in self.services:
            for service in self.services["remote_services"]:
                result = self.check_remote_service(service)
                results["remote_services"].append(result)
                self._update_summary(results["summary"], result)
        
        # Check for state changes and send alerts
        self._process_state_changes(results)
        
        return results
    
    def check_local_service(self, service_config) -> Dict:
        """Check local Docker service"""
        service_name = service_config.get("name")
        container_name = service_config.get("container_name")
        
        result = {
            "name": service_name,
            "type": "docker",
            "status": "unknown",
            "healthy": False,
            "message": "",
            "container_name": container_name,
            "critical": service_config.get("critical", False),
            "checked_at": datetime.now().isoformat()
        }
        
        # Primary check: Docker API
        if not self.docker_client:
            result["status"] = "docker_unavailable"
            result["message"] = "Docker client not available"
            # Fall back to HTTP check if available
            if "health_endpoint" in service_config:
                return self._fallback_to_http_check(service_config, result)
            return result
        
        try:
            # Get container info using Docker API
            container = self.docker_client.containers.get(container_name)
            result["status"] = container.status
            result["container_id"] = container.short_id
            
            if container.status == "running":
                result["healthy"] = True
                
                # Get detailed container info including uptime
                container_info = container.attrs
                created_time = container_info.get('Created')
                if created_time:
                    # Parse creation time and calculate uptime
                    from dateutil import parser
                    created_dt = parser.parse(created_time)
                    uptime = datetime.now(created_dt.tzinfo) - created_dt
                    uptime_str = self._format_uptime(uptime)
                    result["uptime"] = uptime_str
                    result["message"] = f"Container {container_name} running (Up {uptime_str})"
                else:
                    result["message"] = f"Container {container_name} is running"
                
                # Additional health check if endpoint provided
                if "health_endpoint" in service_config:
                    health_result = self._check_http_endpoint(
                        service_config["health_endpoint"],
                        service_config.get("timeout", 10)
                    )
                    if not health_result["healthy"]:
                        result["healthy"] = False
                        result["message"] += f" but health endpoint failed: {health_result['message']}"
                        
            else:
                result["healthy"] = False
                result["message"] = f"Container {container_name} is {container.status}"
                
        except docker.errors.NotFound:
            result["status"] = "container_not_found" 
            result["message"] = f"Container {container_name} not found"
            # Fall back to HTTP check if available
            if "health_endpoint" in service_config:
                return self._fallback_to_http_check(service_config, result)
                
        except docker.errors.APIError as e:
            result["status"] = "docker_api_error"
            result["message"] = f"Docker API error: {str(e)}"
            # Fall back to HTTP check if available
            if "health_endpoint" in service_config:
                return self._fallback_to_http_check(service_config, result)
                
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Error checking container: {str(e)}"
            # Fall back to HTTP check if available
            if "health_endpoint" in service_config:
                return self._fallback_to_http_check(service_config, result)
        
        return result
    
    def _fallback_to_http_check(self, service_config, docker_result) -> Dict:
        """Fallback to HTTP health check when Docker fails"""
        try:
            health_result = self._check_http_endpoint(
                service_config["health_endpoint"],
                service_config.get("timeout", 10)
            )
            
            # Update result to show it's using HTTP fallback
            docker_result["status"] = "http_fallback"
            docker_result["healthy"] = health_result["healthy"]
            
            if health_result["healthy"]:
                docker_result["message"] = f"HTTP health check: {health_result['message']} (Docker: {docker_result['message']})"
            else:
                docker_result["message"] = f"HTTP health check failed: {health_result['message']} (Docker: {docker_result['message']})"
                
        except Exception as e:
            docker_result["message"] += f" and HTTP health check failed: {str(e)}"
            
        return docker_result
    
    def _format_uptime(self, uptime_delta):
        """Format uptime delta to human readable string like docker ps"""
        total_seconds = int(uptime_delta.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds} seconds"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = total_seconds // 86400
            return f"{days} day{'s' if days != 1 else ''}"
    
    def check_remote_service(self, service_config) -> Dict:
        """Check remote service"""
        service_name = service_config.get("name")
        service_type = service_config.get("type", "http")
        
        result = {
            "name": service_name,
            "type": service_type,
            "status": "unknown",
            "healthy": False,
            "message": "",
            "critical": service_config.get("critical", False),
            "checked_at": datetime.now().isoformat()
        }
        
        try:
            if service_type == "http":
                health_result = self._check_http_endpoint(
                    service_config["url"],
                    service_config.get("timeout", 10),
                    service_config.get("expected_status", 200)
                )
                result.update(health_result)
                
            elif service_type == "tcp":
                health_result = self._check_tcp_port(
                    service_config["host"],
                    service_config["port"],
                    service_config.get("timeout", 5)
                )
                result.update(health_result)
                
        except Exception as e:
            result["status"] = "error"
            result["healthy"] = False
            result["message"] = f"Error checking service: {str(e)}"
        
        return result
    
    def _check_http_endpoint(self, url: str, timeout: int = 10, expected_status: int = 200) -> Dict:
        """Check HTTP endpoint health"""
        try:
            response = requests.get(url, timeout=timeout)
            
            if response.status_code == expected_status:
                return {
                    "status": "healthy",
                    "healthy": True,
                    "message": f"HTTP {response.status_code} - Response time: {response.elapsed.total_seconds():.2f}s",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "unhealthy",
                    "healthy": False,
                    "message": f"HTTP {response.status_code} (expected {expected_status})",
                    "response_time": response.elapsed.total_seconds()
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "timeout",
                "healthy": False,
                "message": f"Request timeout after {timeout}s"
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "connection_error",
                "healthy": False,
                "message": "Connection failed"
            }
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "message": f"Request error: {str(e)}"
            }
    
    def _check_tcp_port(self, host: str, port: int, timeout: int = 5) -> Dict:
        """Check TCP port connectivity"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            response_time = time.time() - start_time
            
            if result == 0:
                return {
                    "status": "healthy",
                    "healthy": True,
                    "message": f"Port {port} is open - Response time: {response_time:.2f}s",
                    "response_time": response_time
                }
            else:
                return {
                    "status": "unreachable",
                    "healthy": False,
                    "message": f"Port {port} is closed or unreachable"
                }
                
        except socket.timeout:
            return {
                "status": "timeout",
                "healthy": False,
                "message": f"Connection timeout after {timeout}s"
            }
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "message": f"Connection error: {str(e)}"
            }
    
    def _update_summary(self, summary: Dict, result: Dict):
        """Update summary statistics"""
        summary["total"] += 1
        if result["healthy"]:
            summary["healthy"] += 1
        else:
            summary["unhealthy"] += 1
            if result.get("critical", False):
                summary["critical_down"] += 1
    
    def _process_state_changes(self, current_results: Dict):
        """Process state changes and send alerts"""
        for service_list in ["local_services", "remote_services"]:
            for service in current_results.get(service_list, []):
                service_key = f"{service['name']}_{service['type']}"
                previous_state = self.service_states.get(service_key, {})
                current_healthy = service["healthy"]
                previous_healthy = previous_state.get("healthy")
                
                # Update current state
                self.service_states[service_key] = {
                    "healthy": current_healthy,
                    "last_check": service["checked_at"],
                    "status": service["status"],
                    "message": service["message"]
                }
                
                # Check for state change
                if previous_healthy is not None and previous_healthy != current_healthy:
                    self._send_service_alert(service, current_healthy)
    
    def _send_service_alert(self, service: Dict, is_healthy: bool):
        """Send alert for service state change"""
        service_key = f"{service['name']}_{service['type']}"
        now = datetime.now()
        
        # Check alert cooldown
        last_alert = self.alert_history.get(service_key, {}).get("last_sent")
        if last_alert:
            cooldown = int(self.config.get('ALERT_COOLDOWN', 300))
            if (now - datetime.fromisoformat(last_alert)).total_seconds() < cooldown:
                return
        
        # Prepare alert message
        status = "🟢 RECOVERED" if is_healthy else "🔴 DOWN"
        emoji = "✅" if is_healthy else "❌"
        
        subject = f"[Service Monitor] {status} - {service['name']}"
        
        message = f"""
{emoji} Service Status Change Alert

Service: {service['name']}
Type: {service['type']}
Status: {status}
Time: {service['checked_at']}
Critical: {'Yes' if service.get('critical') else 'No'}

Details: {service['message']}

---
Trigger Deploy Service Monitor
        """.strip()
        
        # Send notifications
        self._send_alert_notifications(subject, message, service)
        
        # Update alert history
        self.alert_history[service_key] = {
            "last_sent": now.isoformat(),
            "status": status,
            "service": service['name']
        }
    
    def _send_alert_notifications(self, subject: str, message: str, service: Dict):
        """Send alert via multiple channels"""
        try:
            # Import notification functions (will be implemented in app.py)
            from app import send_email_notification, send_telegram_notification
            
            # Send email if enabled
            if self.config.get('EMAIL_ENABLED', 'false').lower() == 'true':
                send_email_notification(
                    subject=subject,
                    body=message,
                    is_success=service["healthy"]
                )
            
            # Send Telegram if enabled
            if self.config.get('TELEGRAM_ENABLED', 'false').lower() == 'true':
                send_telegram_notification(
                    message=f"{subject}\n\n{message}"
                )
                
            logger.info(f"Alert sent for service: {service['name']}")
            
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")
    
    def get_service_status(self) -> Dict:
        """Get current status of all services"""
        return self.check_all_services()
    
    def is_monitoring_active(self) -> bool:
        """Check if monitoring is currently active"""
        return self.monitoring_active
    
    def get_service_history(self, service_name: str = None, hours: int = 24) -> List[Dict]:
        """Get service status history (placeholder for future implementation)"""
        # This would typically query a database or log files
        return []

# Global service monitor instance
service_monitor = None

def initialize_service_monitor(config):
    """Initialize global service monitor"""
    global service_monitor
    service_monitor = ServiceMonitor(config)
    return service_monitor
