"""
Health monitoring service for server health checks
"""
import os
import socket
import subprocess
import psutil
from datetime import datetime, timezone
from typing import Dict, List, Optional
from ping3 import ping
from loguru import logger

from models import db
from models.server import Server
from models.health_metric import HealthMetric


class HealthService:
    """Service for monitoring server health"""
    
    def __init__(self):
        self.ping_timeout = int(os.getenv('PING_TIMEOUT', 5))
        self.health_check_interval = int(os.getenv('HEALTH_CHECK_INTERVAL', 60))
    
    def check_server_health(self, server_id: int, detailed: bool = True) -> Dict:
        """
        Perform comprehensive health check on a server
        
        Args:
            server_id: ID of the server to check
            detailed: Whether to perform detailed system metrics check
            
        Returns:
            Dict containing health check results
        """
        try:
            # Get server from database
            server = Server.query.get(server_id)
            if not server:
                raise ValueError(f"Server with ID {server_id} not found")
            
            logger.info(f"Starting health check for {server.alias} ({server.ip})")
            
            # Perform health checks
            health_data = {}
            
            # Basic connectivity check (ping)
            ping_result = self._check_ping(server.ip)
            health_data.update(ping_result)
            
            # DNS resolution check
            dns_result = self._check_dns_resolution(server.ip)
            health_data.update(dns_result)
            
            # If basic checks pass and detailed check is requested
            if ping_result.get('ping_time') is not None and detailed:
                # SSH-based system metrics
                system_metrics = self._get_system_metrics(server)
                health_data.update(system_metrics)
            
            # Create health metric record
            health_metric = HealthMetric.create_health_metric(
                server_id=server_id,
                **health_data
            )
            
            # Update server's last health check time
            server.update_last_health_check()
            
            # Update server status based on health
            if health_metric.is_critical():
                server.update_status('offline')
            elif health_metric.is_warning():
                server.update_status('online')  # Still online but with warnings
            else:
                server.update_status('online')
            
            logger.info(f"Health check completed for {server.alias}: {health_metric.status}")
            
            return {
                'success': True,
                'message': 'Health check completed successfully',
                'data': {
                    'server': server.to_dict(),
                    'health_metric': health_metric.to_dict(),
                    'summary': self._generate_health_summary(health_metric)
                }
            }
            
        except Exception as e:
            logger.error(f"Health check error for server {server_id}: {str(e)}")
            
            # Create error health metric
            try:
                error_metric = HealthMetric.create_health_metric(
                    server_id=server_id,
                    status='critical',
                    error_message=str(e)
                )
                
                # Update server status
                if 'server' in locals():
                    server.update_status('offline')
                
                return {
                    'success': False,
                    'message': f"Health check failed: {str(e)}",
                    'data': {
                        'health_metric': error_metric.to_dict() if error_metric else None
                    }
                }
                
            except Exception as metric_error:
                logger.error(f"Failed to create error metric: {str(metric_error)}")
                return {
                    'success': False,
                    'message': f"Health check failed: {str(e)}",
                    'data': None
                }
    
    def _check_ping(self, ip: str) -> Dict:
        """
        Check server connectivity using ping
        
        Args:
            ip: Server IP address
            
        Returns:
            Dict containing ping results
        """
        try:
            ping_time = ping(ip, timeout=self.ping_timeout)
            
            if ping_time is not None:
                # Convert to milliseconds
                ping_ms = ping_time * 1000
                return {
                    'ping_time': round(ping_ms, 2),
                    'error_message': None
                }
            else:
                return {
                    'ping_time': None,
                    'error_message': 'Ping timeout or host unreachable'
                }
                
        except Exception as e:
            return {
                'ping_time': None,
                'error_message': f"Ping error: {str(e)}"
            }
    
    def _check_dns_resolution(self, ip: str) -> Dict:
        """
        Check DNS resolution for an IP address
        
        Args:
            ip: Server IP address
            
        Returns:
            Dict containing DNS resolution results
        """
        try:
            # Try to resolve hostname from IP
            hostname = socket.gethostbyaddr(ip)[0]
            return {
                'dns_resolved': hostname
            }
        except socket.herror:
            # DNS resolution failed, but this is not necessarily an error
            return {
                'dns_resolved': None
            }
        except Exception as e:
            return {
                'dns_resolved': None,
                'error_message': f"DNS resolution error: {str(e)}"
            }
    
    def _get_system_metrics(self, server: Server) -> Dict:
        """
        Get detailed system metrics via SSH
        
        Args:
            server: Server model instance
            
        Returns:
            Dict containing system metrics
        """
        try:
            import paramiko
            
            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to server
            ssh_client.connect(
                hostname=server.ip,
                port=server.ssh_port,
                username=server.user,
                timeout=self.ping_timeout
            )
            
            metrics = {}
            
            # Get CPU usage
            cpu_command = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
            stdin, stdout, stderr = ssh_client.exec_command(cpu_command)
            cpu_output = stdout.read().decode().strip()
            if cpu_output and cpu_output.replace('.', '').isdigit():
                metrics['cpu_usage'] = float(cpu_output)
            
            # Get memory usage
            mem_command = "free | grep Mem | awk '{printf \"%.2f\", $3/$2 * 100.0}'"
            stdin, stdout, stderr = ssh_client.exec_command(mem_command)
            mem_output = stdout.read().decode().strip()
            if mem_output and mem_output.replace('.', '').isdigit():
                metrics['memory_usage'] = float(mem_output)
            
            # Get disk usage
            disk_command = "df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1"
            stdin, stdout, stderr = ssh_client.exec_command(disk_command)
            disk_output = stdout.read().decode().strip()
            if disk_output and disk_output.isdigit():
                metrics['disk_usage'] = float(disk_output)
            
            # Get uptime
            uptime_command = "cat /proc/uptime | awk '{print int($1)}'"
            stdin, stdout, stderr = ssh_client.exec_command(uptime_command)
            uptime_output = stdout.read().decode().strip()
            if uptime_output and uptime_output.isdigit():
                metrics['uptime'] = int(uptime_output)
            
            # Get load average
            load_command = "cat /proc/loadavg | awk '{print $1}'"
            stdin, stdout, stderr = ssh_client.exec_command(load_command)
            load_output = stdout.read().decode().strip()
            if load_output and load_output.replace('.', '').isdigit():
                metrics['load_average'] = float(load_output)
            
            ssh_client.close()
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Failed to get system metrics for {server.alias}: {str(e)}")
            return {
                'error_message': f"System metrics error: {str(e)}"
            }
    
    def _generate_health_summary(self, health_metric: HealthMetric) -> Dict:
        """
        Generate human-readable health summary
        
        Args:
            health_metric: HealthMetric instance
            
        Returns:
            Dict containing health summary
        """
        summary = {
            'overall_status': health_metric.status,
            'issues': [],
            'recommendations': []
        }
        
        # Check for issues and generate recommendations
        if health_metric.cpu_usage and health_metric.cpu_usage > 90:
            summary['issues'].append(f"High CPU usage: {health_metric.cpu_usage}%")
            summary['recommendations'].append("Consider optimizing CPU-intensive processes")
        
        if health_metric.memory_usage and health_metric.memory_usage > 90:
            summary['issues'].append(f"High memory usage: {health_metric.memory_usage}%")
            summary['recommendations'].append("Consider adding more RAM or optimizing memory usage")
        
        if health_metric.disk_usage and health_metric.disk_usage > 90:
            summary['issues'].append(f"High disk usage: {health_metric.disk_usage}%")
            summary['recommendations'].append("Consider cleaning up disk space or adding storage")
        
        if health_metric.ping_time and health_metric.ping_time > 500:
            summary['issues'].append(f"High latency: {health_metric.ping_time}ms")
            summary['recommendations'].append("Check network connectivity and routing")
        
        if health_metric.error_message:
            summary['issues'].append(f"System error: {health_metric.error_message}")
            summary['recommendations'].append("Check server logs and system status")
        
        return summary
    
    def get_server_health_history(self, server_id: int, hours: int = 24) -> Dict:
        """
        Get health history for a server
        
        Args:
            server_id: ID of the server
            hours: Number of hours to look back
            
        Returns:
            Dict containing health history and summary
        """
        try:
            server = Server.query.get(server_id)
            if not server:
                raise ValueError(f"Server with ID {server_id} not found")
            
            # Get health metrics
            metrics = HealthMetric.get_latest_metrics(server_id=server_id, limit=100)
            
            # Get health summary
            health_summary = HealthMetric.get_server_health_summary(server_id, hours)
            
            return {
                'success': True,
                'message': 'Health history retrieved successfully',
                'data': {
                    'server': server.to_dict(),
                    'metrics': [metric.to_dict() for metric in metrics],
                    'summary': health_summary
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get health history for server {server_id}: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to get health history: {str(e)}",
                'data': None
            }
    
    def check_all_servers_health(self) -> Dict:
        """
        Perform health check on all active servers
        
        Returns:
            Dict containing aggregated health check results
        """
        try:
            active_servers = Server.get_active_servers()
            
            if not active_servers:
                return {
                    'success': True,
                    'message': 'No active servers to check',
                    'data': {
                        'total_servers': 0,
                        'results': []
                    }
                }
            
            results = []
            for server in active_servers:
                result = self.check_server_health(server.id, detailed=False)
                results.append({
                    'server_id': server.id,
                    'server_alias': server.alias,
                    'result': result
                })
            
            # Calculate summary statistics
            total_servers = len(results)
            healthy_servers = sum(1 for r in results if r['result'].get('success') and 
                                r['result'].get('data', {}).get('health_metric', {}).get('status') == 'healthy')
            warning_servers = sum(1 for r in results if r['result'].get('success') and 
                                r['result'].get('data', {}).get('health_metric', {}).get('status') == 'warning')
            critical_servers = sum(1 for r in results if not r['result'].get('success') or 
                                 r['result'].get('data', {}).get('health_metric', {}).get('status') == 'critical')
            
            return {
                'success': True,
                'message': f'Health check completed for {total_servers} servers',
                'data': {
                    'total_servers': total_servers,
                    'healthy_servers': healthy_servers,
                    'warning_servers': warning_servers,
                    'critical_servers': critical_servers,
                    'results': results
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to check all servers health: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to check servers health: {str(e)}",
                'data': None
            }
