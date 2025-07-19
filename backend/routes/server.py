"""
Server management API routes
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from loguru import logger

from services.server_service import ServerService
from schemas import (
    ServerCreateSchema, ServerUpdateSchema, PaginationSchema,
    BaseResponseModel, ErrorResponseSchema
)

# Create namespace
server_bp = Namespace('servers', description='Server management operations')

# Initialize service
server_service = ServerService()

# Define models for Swagger documentation
server_model = server_bp.model('Server', {
    'id': fields.Integer(description='Server ID'),
    'ip': fields.String(required=True, description='Server IP address'),
    'alias': fields.String(required=True, description='Server alias'),
    'name': fields.String(required=True, description='Server name'),
    'user': fields.String(required=True, description='SSH username'),
    'script_path': fields.String(required=True, description='Deployment script path'),
    'ssh_port': fields.Integer(description='SSH port', default=22),
    'description': fields.String(description='Server description'),
    'environment': fields.String(description='Environment', enum=['production', 'staging', 'development']),
    'status': fields.String(description='Server status'),
    'is_active': fields.Boolean(description='Whether server is active'),
    'created_at': fields.String(description='Creation timestamp'),
    'updated_at': fields.String(description='Update timestamp'),
    'last_deployed': fields.String(description='Last deployment timestamp'),
    'last_health_check': fields.String(description='Last health check timestamp')
})

server_create_model = server_bp.model('ServerCreate', {
    'ip': fields.String(required=True, description='Server IP address'),
    'alias': fields.String(required=True, description='Server alias'),
    'name': fields.String(required=True, description='Server name'),
    'user': fields.String(required=True, description='SSH username'),
    'script_path': fields.String(required=True, description='Deployment script path'),
    'ssh_port': fields.Integer(description='SSH port', default=22),
    'description': fields.String(description='Server description'),
    'environment': fields.String(description='Environment', enum=['production', 'staging', 'development'])
})

server_update_model = server_bp.model('ServerUpdate', {
    'ip': fields.String(description='Server IP address'),
    'alias': fields.String(description='Server alias'),
    'name': fields.String(description='Server name'),
    'user': fields.String(description='SSH username'),
    'script_path': fields.String(description='Deployment script path'),
    'ssh_port': fields.Integer(description='SSH port'),
    'description': fields.String(description='Server description'),
    'environment': fields.String(description='Environment'),
    'is_active': fields.Boolean(description='Whether server is active')
})

response_model = server_bp.model('Response', {
    'success': fields.Boolean(description='Request success status'),
    'message': fields.String(description='Response message'),
    'data': fields.Raw(description='Response data')
})


@server_bp.route('/')
class ServerList(Resource):
    """Server list and creation endpoints"""
    
    @server_bp.doc('list_servers')
    @server_bp.marshal_with(response_model)
    @server_bp.param('page', 'Page number', type=int, default=1)
    @server_bp.param('per_page', 'Items per page', type=int, default=50)
    @server_bp.param('active_only', 'Show only active servers', type=bool, default=True)
    @server_bp.param('environment', 'Filter by environment', type=str)
    @jwt_required()
    def get(self):
        """Get list of servers with pagination"""
        try:
            # Parse query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            active_only = request.args.get('active_only', True, type=bool)
            environment = request.args.get('environment')
            
            # Get servers
            result = server_service.get_servers(
                active_only=active_only,
                environment=environment,
                page=page,
                per_page=per_page
            )
            
            return result, 200 if result['success'] else 400
            
        except Exception as e:
            logger.error(f"Failed to get servers: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to retrieve servers: {str(e)}',
                'data': None
            }, 500
    
    @server_bp.doc('create_server')
    @server_bp.expect(server_create_model)
    @server_bp.marshal_with(response_model)
    @jwt_required()
    def post(self):
        """Create a new server"""
        try:
            # Get current user ID
            current_user_id = get_jwt_identity()
            
            # Validate input data
            data = request.get_json()
            try:
                server_data = ServerCreateSchema(**data)
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Validation error: {str(e)}',
                    'data': None
                }, 400
            
            # Create server
            result = server_service.create_server(
                data=server_data.dict(),
                created_by=current_user_id
            )
            
            return result, 201 if result['success'] else 400
            
        except Exception as e:
            logger.error(f"Failed to create server: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to create server: {str(e)}',
                'data': None
            }, 500


@server_bp.route('/<int:server_id>')
class ServerDetail(Resource):
    """Server detail, update, and delete endpoints"""
    
    @server_bp.doc('get_server')
    @server_bp.marshal_with(response_model)
    @server_bp.param('include_relations', 'Include related data', type=bool, default=False)
    @jwt_required()
    def get(self, server_id):
        """Get server details"""
        try:
            include_relations = request.args.get('include_relations', False, type=bool)
            
            result = server_service.get_server(
                server_id=server_id,
                include_relations=include_relations
            )
            
            return result, 200 if result['success'] else 404
            
        except Exception as e:
            logger.error(f"Failed to get server {server_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to retrieve server: {str(e)}',
                'data': None
            }, 500
    
    @server_bp.doc('update_server')
    @server_bp.expect(server_update_model)
    @server_bp.marshal_with(response_model)
    @jwt_required()
    def put(self, server_id):
        """Update server"""
        try:
            # Get current user ID
            current_user_id = get_jwt_identity()
            
            # Validate input data
            data = request.get_json()
            try:
                server_data = ServerUpdateSchema(**data)
            except Exception as e:
                return {
                    'success': False,
                    'message': f'Validation error: {str(e)}',
                    'data': None
                }, 400
            
            # Update server
            result = server_service.update_server(
                server_id=server_id,
                data=server_data.dict(exclude_unset=True),
                updated_by=current_user_id
            )
            
            return result, 200 if result['success'] else 400
            
        except Exception as e:
            logger.error(f"Failed to update server {server_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to update server: {str(e)}',
                'data': None
            }, 500
    
    @server_bp.doc('delete_server')
    @server_bp.marshal_with(response_model)
    @jwt_required()
    def delete(self, server_id):
        """Delete server (soft delete)"""
        try:
            # Get current user ID
            current_user_id = get_jwt_identity()
            
            result = server_service.delete_server(
                server_id=server_id,
                deleted_by=current_user_id
            )
            
            return result, 200 if result['success'] else 400
            
        except Exception as e:
            logger.error(f"Failed to delete server {server_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to delete server: {str(e)}',
                'data': None
            }, 500


@server_bp.route('/search')
class ServerSearch(Resource):
    """Server search endpoint"""
    
    @server_bp.doc('search_servers')
    @server_bp.marshal_with(response_model)
    @server_bp.param('q', 'Search query', type=str, required=True)
    @server_bp.param('environment', 'Filter by environment', type=str)
    @server_bp.param('status', 'Filter by status', type=str)
    @server_bp.param('is_active', 'Filter by active status', type=bool)
    @jwt_required()
    def get(self):
        """Search servers"""
        try:
            query = request.args.get('q', '').strip()
            if not query:
                return {
                    'success': False,
                    'message': 'Search query is required',
                    'data': None
                }, 400
            
            # Build filters
            filters = {}
            if request.args.get('environment'):
                filters['environment'] = request.args.get('environment')
            if request.args.get('status'):
                filters['status'] = request.args.get('status')
            if request.args.get('is_active') is not None:
                filters['is_active'] = request.args.get('is_active', type=bool)
            
            result = server_service.search_servers(
                query=query,
                filters=filters if filters else None
            )
            
            return result, 200 if result['success'] else 400
            
        except Exception as e:
            logger.error(f"Failed to search servers: {str(e)}")
            return {
                'success': False,
                'message': f'Search failed: {str(e)}',
                'data': None
            }, 500


@server_bp.route('/statistics')
class ServerStatistics(Resource):
    """Server statistics endpoint"""
    
    @server_bp.doc('get_server_statistics')
    @server_bp.marshal_with(response_model)
    @jwt_required()
    def get(self):
        """Get server statistics"""
        try:
            result = server_service.get_server_statistics()
            return result, 200 if result['success'] else 400
            
        except Exception as e:
            logger.error(f"Failed to get server statistics: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to retrieve statistics: {str(e)}',
                'data': None
            }, 500
