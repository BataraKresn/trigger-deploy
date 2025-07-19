"""
Server management service for CRUD operations on servers
"""
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from loguru import logger

from models import db
from models.server import Server
from models.user import User


class ServerService:
    """Service for managing servers"""
    
    def __init__(self):
        self.ip_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )
    
    def create_server(self, data: Dict, created_by: Optional[int] = None) -> Dict:
        """
        Create a new server
        
        Args:
            data: Server data dictionary
            created_by: ID of user creating the server
            
        Returns:
            Dict containing creation result
        """
        try:
            # Validate required fields
            required_fields = ['ip', 'alias', 'name', 'user', 'script_path']
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f"Field '{field}' is required")
            
            # Validate IP address
            if not self._is_valid_ip(data['ip']):
                raise ValueError("Invalid IP address format")
            
            # Validate SSH port
            ssh_port = data.get('ssh_port', 22)
            if not isinstance(ssh_port, int) or ssh_port < 1 or ssh_port > 65535:
                raise ValueError("Invalid SSH port (must be between 1 and 65535)")
            
            # Check for duplicate IP + port combination
            existing_server = Server.find_by_ip(data['ip'], ssh_port)
            if existing_server:
                raise ValueError(f"Server with IP {data['ip']}:{ssh_port} already exists")
            
            # Check for duplicate alias
            existing_alias = Server.find_by_alias(data['alias'])
            if existing_alias:
                raise ValueError(f"Server with alias '{data['alias']}' already exists")
            
            # Create server
            server = Server.create_server(
                ip=data['ip'],
                alias=data['alias'],
                name=data['name'],
                user=data['user'],
                script_path=data['script_path'],
                ssh_port=ssh_port,
                description=data.get('description'),
                environment=data.get('environment', 'production'),
                created_by=created_by
            )
            
            logger.info(f"Server {server.alias} ({server.ip}) created successfully")
            
            return {
                'success': True,
                'message': 'Server created successfully',
                'data': server.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to create server: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to create server: {str(e)}",
                'data': None
            }
    
    def get_server(self, server_id: int, include_relations: bool = False) -> Dict:
        """
        Get a server by ID
        
        Args:
            server_id: ID of the server
            include_relations: Whether to include related data
            
        Returns:
            Dict containing server data
        """
        try:
            server = Server.query.get(server_id)
            if not server:
                raise ValueError(f"Server with ID {server_id} not found")
            
            return {
                'success': True,
                'message': 'Server retrieved successfully',
                'data': server.to_dict(include_relations=include_relations)
            }
            
        except Exception as e:
            logger.error(f"Failed to get server {server_id}: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to retrieve server: {str(e)}",
                'data': None
            }
    
    def get_servers(self, active_only: bool = True, environment: Optional[str] = None,
                   page: int = 1, per_page: int = 50) -> Dict:
        """
        Get list of servers with pagination
        
        Args:
            active_only: Whether to return only active servers
            environment: Filter by environment
            page: Page number (1-based)
            per_page: Number of servers per page
            
        Returns:
            Dict containing paginated server list
        """
        try:
            query = Server.query
            
            # Apply filters
            if active_only:
                query = query.filter_by(is_active=True)
            
            if environment:
                query = query.filter_by(environment=environment)
            
            # Order by creation date (newest first)
            query = query.order_by(db.desc(Server.created_at))
            
            # Paginate
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            servers = [server.to_dict() for server in pagination.items]
            
            return {
                'success': True,
                'message': f'Retrieved {len(servers)} servers',
                'data': {
                    'servers': servers,
                    'pagination': {
                        'page': pagination.page,
                        'per_page': pagination.per_page,
                        'total': pagination.total,
                        'pages': pagination.pages,
                        'has_next': pagination.has_next,
                        'has_prev': pagination.has_prev
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get servers: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to retrieve servers: {str(e)}",
                'data': None
            }
    
    def update_server(self, server_id: int, data: Dict, 
                     updated_by: Optional[int] = None) -> Dict:
        """
        Update an existing server
        
        Args:
            server_id: ID of the server to update
            data: Updated server data
            updated_by: ID of user updating the server
            
        Returns:
            Dict containing update result
        """
        try:
            server = Server.query.get(server_id)
            if not server:
                raise ValueError(f"Server with ID {server_id} not found")
            
            # Fields that can be updated
            updatable_fields = [
                'alias', 'name', 'user', 'script_path', 'ssh_port',
                'description', 'environment', 'is_active'
            ]
            
            # Check for conflicts before updating
            if 'ip' in data and data['ip'] != server.ip:
                # Validate new IP
                if not self._is_valid_ip(data['ip']):
                    raise ValueError("Invalid IP address format")
                
                # Check for duplicate
                ssh_port = data.get('ssh_port', server.ssh_port)
                existing_server = Server.find_by_ip(data['ip'], ssh_port)
                if existing_server and existing_server.id != server.id:
                    raise ValueError(f"Server with IP {data['ip']}:{ssh_port} already exists")
                
                server.ip = data['ip']
            
            if 'alias' in data and data['alias'] != server.alias:
                # Check for duplicate alias
                existing_alias = Server.find_by_alias(data['alias'])
                if existing_alias and existing_alias.id != server.id:
                    raise ValueError(f"Server with alias '{data['alias']}' already exists")
                
                server.alias = data['alias']
            
            # Update other fields
            for field in updatable_fields:
                if field in data:
                    setattr(server, field, data[field])
            
            # Validate SSH port if updated
            if hasattr(server, 'ssh_port'):
                if not isinstance(server.ssh_port, int) or server.ssh_port < 1 or server.ssh_port > 65535:
                    raise ValueError("Invalid SSH port (must be between 1 and 65535)")
            
            # Update timestamp
            server.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            logger.info(f"Server {server.alias} updated successfully")
            
            return {
                'success': True,
                'message': 'Server updated successfully',
                'data': server.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update server {server_id}: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to update server: {str(e)}",
                'data': None
            }
    
    def delete_server(self, server_id: int, deleted_by: Optional[int] = None) -> Dict:
        """
        Delete a server (soft delete by setting is_active=False)
        
        Args:
            server_id: ID of the server to delete
            deleted_by: ID of user deleting the server
            
        Returns:
            Dict containing deletion result
        """
        try:
            server = Server.query.get(server_id)
            if not server:
                raise ValueError(f"Server with ID {server_id} not found")
            
            # Check if server is currently deploying
            if server.is_deploying():
                raise ValueError("Cannot delete server while deployment is in progress")
            
            # Soft delete (set as inactive)
            server.is_active = False
            server.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            logger.info(f"Server {server.alias} ({server.ip}) deleted successfully")
            
            return {
                'success': True,
                'message': 'Server deleted successfully',
                'data': server.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete server {server_id}: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to delete server: {str(e)}",
                'data': None
            }
    
    def get_server_statistics(self) -> Dict:
        """
        Get server statistics and summary
        
        Returns:
            Dict containing server statistics
        """
        try:
            total_servers = Server.query.count()
            active_servers = Server.query.filter_by(is_active=True).count()
            inactive_servers = total_servers - active_servers
            
            # Count by status
            online_servers = Server.query.filter_by(status='online', is_active=True).count()
            offline_servers = Server.query.filter_by(status='offline', is_active=True).count()
            deploying_servers = Server.query.filter_by(status='deploying', is_active=True).count()
            error_servers = Server.query.filter_by(status='error', is_active=True).count()
            
            # Count by environment
            environments = db.session.query(
                Server.environment,
                db.func.count(Server.id).label('count')
            ).filter_by(is_active=True).group_by(Server.environment).all()
            
            environment_stats = {env: count for env, count in environments}
            
            return {
                'success': True,
                'message': 'Server statistics retrieved successfully',
                'data': {
                    'total_servers': total_servers,
                    'active_servers': active_servers,
                    'inactive_servers': inactive_servers,
                    'status_distribution': {
                        'online': online_servers,
                        'offline': offline_servers,
                        'deploying': deploying_servers,
                        'error': error_servers
                    },
                    'environment_distribution': environment_stats,
                    'health_percentage': round((online_servers / active_servers * 100) if active_servers > 0 else 0, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get server statistics: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to retrieve statistics: {str(e)}",
                'data': None
            }
    
    def search_servers(self, query: str, filters: Optional[Dict] = None) -> Dict:
        """
        Search servers by name, alias, IP, or description
        
        Args:
            query: Search query string
            filters: Additional filters (environment, status, etc.)
            
        Returns:
            Dict containing search results
        """
        try:
            search_query = Server.query
            
            # Apply text search
            if query:
                search_filter = db.or_(
                    Server.name.ilike(f'%{query}%'),
                    Server.alias.ilike(f'%{query}%'),
                    Server.ip.ilike(f'%{query}%'),
                    Server.description.ilike(f'%{query}%')
                )
                search_query = search_query.filter(search_filter)
            
            # Apply additional filters
            if filters:
                if filters.get('environment'):
                    search_query = search_query.filter_by(environment=filters['environment'])
                
                if filters.get('status'):
                    search_query = search_query.filter_by(status=filters['status'])
                
                if filters.get('is_active') is not None:
                    search_query = search_query.filter_by(is_active=filters['is_active'])
            
            # Default to active servers only
            if not filters or filters.get('is_active') is None:
                search_query = search_query.filter_by(is_active=True)
            
            servers = search_query.order_by(Server.name).all()
            
            return {
                'success': True,
                'message': f'Found {len(servers)} servers matching "{query}"',
                'data': {
                    'servers': [server.to_dict() for server in servers],
                    'total_count': len(servers),
                    'search_query': query,
                    'filters_applied': filters or {}
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to search servers: {str(e)}")
            return {
                'success': False,
                'message': f"Search failed: {str(e)}",
                'data': None
            }
    
    def _is_valid_ip(self, ip: str) -> bool:
        """
        Validate IP address format
        
        Args:
            ip: IP address string
            
        Returns:
            Boolean indicating if IP is valid
        """
        try:
            # Basic IPv4 validation
            if self.ip_pattern.match(ip):
                return True
            
            # Try IPv6 validation
            import ipaddress
            ipaddress.IPv6Address(ip)
            return True
            
        except:
            return False
