"""
Deployment service for managing server deployments
"""
import os
import subprocess
import tempfile
import paramiko
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from loguru import logger

from models import db
from models.server import Server
from models.deploy_log import DeployLog
from models.user import User


class DeploymentService:
    """Service for handling server deployments"""
    
    def __init__(self):
        self.ssh_timeout = int(os.getenv('DEFAULT_SSH_TIMEOUT', 30))
        self.max_deploy_time = int(os.getenv('MAX_DEPLOY_TIME', 300))
    
    def deploy_to_server(self, server_id: int, user_id: Optional[int] = None, 
                        command: Optional[str] = None) -> Dict:
        """
        Deploy to a specific server
        
        Args:
            server_id: ID of the target server
            user_id: ID of user executing deployment
            command: Optional custom command to execute
            
        Returns:
            Dict containing deployment result
        """
        try:
            # Get server from database
            server = Server.query.get(server_id)
            if not server:
                raise ValueError(f"Server with ID {server_id} not found")
            
            if not server.is_active:
                raise ValueError(f"Server {server.alias} is not active")
            
            # Check if server is already deploying
            if server.is_deploying():
                raise ValueError(f"Server {server.alias} is already deploying")
            
            # Create deployment log
            deploy_log = DeployLog.create_deployment_log(
                server_id=server_id,
                executed_by=user_id,
                command=command or server.script_path,
                deployment_type='manual'
            )
            
            # Update server status
            server.update_status('deploying')
            
            logger.info(f"Starting deployment to {server.alias} ({server.ip})")
            
            # Execute deployment
            result = self._execute_deployment(server, deploy_log)
            
            # Update deployment log with result
            if result['success']:
                deploy_log.complete_deployment(
                    status='success',
                    output=result['output']
                )
                server.update_status('online')
                server.update_last_deployed()
                logger.info(f"Deployment to {server.alias} completed successfully")
            else:
                deploy_log.complete_deployment(
                    status='error',
                    output=result['output'],
                    error_message=result['error']
                )
                server.update_status('error')
                logger.error(f"Deployment to {server.alias} failed: {result['error']}")
            
            return {
                'success': result['success'],
                'message': 'Deployment completed successfully' if result['success'] 
                          else f"Deployment failed: {result['error']}",
                'data': {
                    'deploy_log_id': deploy_log.id,
                    'server': server.to_dict(),
                    'output': result['output'],
                    'duration': deploy_log.duration
                }
            }
            
        except Exception as e:
            logger.error(f"Deployment error: {str(e)}")
            
            # Update server status if deployment log exists
            if 'deploy_log' in locals():
                deploy_log.complete_deployment(
                    status='error',
                    error_message=str(e)
                )
            
            # Reset server status
            if 'server' in locals():
                server.update_status('error')
            
            return {
                'success': False,
                'message': f"Deployment failed: {str(e)}",
                'data': None
            }
    
    def _execute_deployment(self, server: Server, deploy_log: DeployLog) -> Dict:
        """
        Execute deployment using SSH
        
        Args:
            server: Server model instance
            deploy_log: DeployLog model instance
            
        Returns:
            Dict containing execution result
        """
        output_lines = []
        
        try:
            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to server
            output_lines.append(f"Connecting to {server.user}@{server.ip}:{server.ssh_port}")
            deploy_log.update_output('\n'.join(output_lines))
            
            ssh_client.connect(
                hostname=server.ip,
                port=server.ssh_port,
                username=server.user,
                timeout=self.ssh_timeout
            )
            
            output_lines.append("SSH connection established")
            deploy_log.update_output('\n'.join(output_lines))
            
            # Execute deployment script
            command = deploy_log.command or server.script_path
            output_lines.append(f"Executing: {command}")
            deploy_log.update_output('\n'.join(output_lines))
            
            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=self.max_deploy_time)
            
            # Read output in real-time
            while True:
                line = stdout.readline()
                if not line:
                    break
                output_lines.append(line.strip())
                # Update deploy log periodically
                if len(output_lines) % 10 == 0:
                    deploy_log.update_output('\n'.join(output_lines))
            
            # Get exit code
            exit_code = stdout.channel.recv_exit_status()
            
            # Read any remaining stderr
            error_output = stderr.read().decode('utf-8').strip()
            if error_output:
                output_lines.append(f"STDERR: {error_output}")
            
            ssh_client.close()
            
            output_lines.append(f"Command completed with exit code: {exit_code}")
            final_output = '\n'.join(output_lines)
            
            if exit_code == 0:
                output_lines.append("✅ Deployment completed successfully")
                return {
                    'success': True,
                    'output': '\n'.join(output_lines),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'output': final_output,
                    'error': f"Command failed with exit code {exit_code}"
                }
                
        except paramiko.AuthenticationException as e:
            error_msg = f"SSH authentication failed: {str(e)}"
            output_lines.append(f"❌ {error_msg}")
            return {
                'success': False,
                'output': '\n'.join(output_lines),
                'error': error_msg
            }
            
        except paramiko.SSHException as e:
            error_msg = f"SSH connection error: {str(e)}"
            output_lines.append(f"❌ {error_msg}")
            return {
                'success': False,
                'output': '\n'.join(output_lines),
                'error': error_msg
            }
            
        except Exception as e:
            error_msg = f"Deployment execution error: {str(e)}"
            output_lines.append(f"❌ {error_msg}")
            return {
                'success': False,
                'output': '\n'.join(output_lines),
                'error': error_msg
            }
        
        finally:
            # Ensure SSH client is closed
            try:
                ssh_client.close()
            except:
                pass
    
    def get_deployment_logs(self, server_id: Optional[int] = None, 
                          limit: int = 50, status: Optional[str] = None) -> List[Dict]:
        """
        Get deployment logs with optional filters
        
        Args:
            server_id: Filter by server ID
            limit: Maximum number of logs to return
            status: Filter by deployment status
            
        Returns:
            List of deployment log dictionaries
        """
        logs = DeployLog.get_recent_logs(limit=limit, server_id=server_id, status=status)
        return [log.to_dict() for log in logs]
    
    def get_deployment_stats(self, server_id: Optional[int] = None, days: int = 30) -> Dict:
        """
        Get deployment statistics
        
        Args:
            server_id: Filter by server ID
            days: Number of days to look back
            
        Returns:
            Dictionary containing deployment statistics
        """
        return DeployLog.get_deployment_stats(server_id=server_id, days=days)
    
    def cancel_deployment(self, deploy_log_id: int, user_id: Optional[int] = None) -> Dict:
        """
        Cancel an ongoing deployment
        
        Args:
            deploy_log_id: ID of deployment log to cancel
            user_id: ID of user requesting cancellation
            
        Returns:
            Dict containing cancellation result
        """
        try:
            deploy_log = DeployLog.query.get(deploy_log_id)
            if not deploy_log:
                raise ValueError(f"Deployment log with ID {deploy_log_id} not found")
            
            if not deploy_log.is_running():
                raise ValueError("Deployment is not currently running")
            
            # Mark as cancelled
            deploy_log.complete_deployment(
                status='cancelled',
                error_message=f"Cancelled by user {user_id}" if user_id else "Cancelled"
            )
            
            # Update server status
            server = deploy_log.server
            server.update_status('online')
            
            logger.info(f"Deployment {deploy_log_id} cancelled")
            
            return {
                'success': True,
                'message': 'Deployment cancelled successfully',
                'data': deploy_log.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Cancellation error: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to cancel deployment: {str(e)}",
                'data': None
            }
