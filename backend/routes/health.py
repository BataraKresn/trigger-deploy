from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.health_service import HealthService
from schemas import HealthCheckResponseSchema
import logging

logger = logging.getLogger(__name__)

# Create namespace
health_ns = Namespace('health', description='Health check operations')
from schemas import HealthCheckResponseSchema
import logging

logger = logging.getLogger(__name__)

# Create namespace
health_ns = Namespace('health', description='Health check operations')

# API Models for documentation
health_response_model = health_ns.model('HealthResponse', {
    'id': fields.Integer(description='Health check ID'),
    'server_alias': fields.String(description='Server alias'),
    'status': fields.String(description='Health status'),
    'response_time': fields.Float(description='Response time in seconds'),
    'checked_at': fields.DateTime(description='Check timestamp'),
    'error_message': fields.String(description='Error message if failed')
})

health_list_model = health_ns.model('HealthList', {
    'checks': fields.List(fields.Nested(health_response_model)),
    'total': fields.Integer(description='Total number of health checks'),
    'page': fields.Integer(description='Current page'),
    'per_page': fields.Integer(description='Items per page'),
    'pages': fields.Integer(description='Total pages')
})

health_stats_model = health_ns.model('HealthStats', {
    'total_checks': fields.Integer(description='Total health checks'),
    'healthy_servers': fields.Integer(description='Number of healthy servers'),
    'unhealthy_servers': fields.Integer(description='Number of unhealthy servers'),
    'avg_response_time': fields.Float(description='Average response time'),
    'recent_checks': fields.List(fields.Nested(health_response_model))
})

server_health_model = health_ns.model('ServerHealth', {
    'server_alias': fields.String(description='Server alias'),
    'status': fields.String(description='Current health status'),
    'last_check': fields.DateTime(description='Last health check'),
    'response_time': fields.Float(description='Last response time'),
    'uptime_percentage': fields.Float(description='Uptime percentage'),
    'recent_checks': fields.List(fields.Nested(health_response_model))
})

@health_ns.route('')
class HealthList(Resource):
    @health_ns.doc('list_health_checks')
    @health_ns.marshal_with(health_list_model)
    @health_ns.param('page', 'Page number', type=int, default=1)
    @health_ns.param('per_page', 'Items per page', type=int, default=20)
    @health_ns.param('server_alias', 'Filter by server alias', type=str)
    @health_ns.param('status', 'Filter by status', type=str)
    @jwt_required()
    def get(self):
        """Get list of health checks with filtering and pagination"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            filters = {}
            if request.args.get('server_alias'):
                filters['server_alias'] = request.args.get('server_alias')
            if request.args.get('status'):
                filters['status'] = request.args.get('status')
            
            result = HealthService.get_health_checks(
                page=page,
                per_page=per_page,
                **filters
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting health checks: {str(e)}")
            health_ns.abort(500, f"Error getting health checks: {str(e)}")

@health_ns.route('/check')
class HealthCheck(Resource):
    @health_ns.doc('trigger_health_check')
    @health_ns.param('server_alias', 'Server alias to check (optional, checks all if not provided)', type=str)
    @jwt_required()
    def post(self):
        """Trigger health check for servers"""
        try:
            server_alias = request.args.get('server_alias')
            
            if server_alias:
                result = HealthService.check_server_health(server_alias)
                return {"message": f"Health check triggered for {server_alias}", "result": result}
            else:
                result = HealthService.check_all_servers_health()
                return {"message": "Health check triggered for all servers", "results": result}
            
        except Exception as e:
            logger.error(f"Error triggering health check: {str(e)}")
            health_ns.abort(500, f"Error triggering health check: {str(e)}")

@health_ns.route('/stats')
class HealthStats(Resource):
    @health_ns.doc('get_health_stats')
    @health_ns.marshal_with(health_stats_model)
    @jwt_required()
    def get(self):
        """Get health check statistics"""
        try:
            result = HealthService.get_health_stats()
            return result
            
        except Exception as e:
            logger.error(f"Error getting health stats: {str(e)}")
            health_ns.abort(500, f"Error getting health stats: {str(e)}")

@health_ns.route('/server/<string:server_alias>')
class ServerHealth(Resource):
    @health_ns.doc('get_server_health')
    @health_ns.marshal_with(server_health_model)
    @jwt_required()
    def get(self, server_alias):
        """Get health status for specific server"""
        try:
            result = HealthService.get_server_health_status(server_alias)
            if not result:
                health_ns.abort(404, "Server not found")
            return result
            
        except Exception as e:
            logger.error(f"Error getting server health {server_alias}: {str(e)}")
            health_ns.abort(500, f"Error getting server health: {str(e)}")

@health_ns.route('/system')
class SystemHealth(Resource):
    @health_ns.doc('get_system_health')
    def get(self):
        """Get system health status (public endpoint)"""
        try:
            result = HealthService.get_system_health()
            return result
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            health_ns.abort(500, f"Error getting system health: {str(e)}")
