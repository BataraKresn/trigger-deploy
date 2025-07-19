from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.log_service import LogService
from schemas import LogResponseSchema
import logging

logger = logging.getLogger(__name__)

# Create namespace
logs_ns = Namespace('logs', description='Log operations')

# API Models for documentation
log_response_model = logs_ns.model('LogResponse', {
    'id': fields.Integer(description='Log ID'),
    'level': fields.String(description='Log level'),
    'message': fields.String(description='Log message'),
    'timestamp': fields.DateTime(description='Log timestamp'),
    'source': fields.String(description='Log source'),
    'server_alias': fields.String(description='Server alias'),
    'deploy_id': fields.Integer(description='Related deployment ID')
})

log_list_model = logs_ns.model('LogList', {
    'logs': fields.List(fields.Nested(log_response_model)),
    'total': fields.Integer(description='Total number of logs'),
    'page': fields.Integer(description='Current page'),
    'per_page': fields.Integer(description='Items per page'),
    'pages': fields.Integer(description='Total pages')
})

log_stats_model = logs_ns.model('LogStats', {
    'total_logs': fields.Integer(description='Total number of logs'),
    'error_logs': fields.Integer(description='Number of error logs'),
    'warning_logs': fields.Integer(description='Number of warning logs'),
    'info_logs': fields.Integer(description='Number of info logs'),
    'recent_errors': fields.List(fields.Nested(log_response_model))
})

@logs_ns.route('')
class LogList(Resource):
    @logs_ns.doc('list_logs')
    @logs_ns.marshal_with(log_list_model)
    @logs_ns.param('page', 'Page number', type=int, default=1)
    @logs_ns.param('per_page', 'Items per page', type=int, default=20)
    @logs_ns.param('level', 'Filter by log level', type=str)
    @logs_ns.param('source', 'Filter by log source', type=str)
    @logs_ns.param('server_alias', 'Filter by server alias', type=str)
    @logs_ns.param('deploy_id', 'Filter by deployment ID', type=int)
    @logs_ns.param('start_date', 'Filter from date (ISO format)', type=str)
    @logs_ns.param('end_date', 'Filter to date (ISO format)', type=str)
    @jwt_required()
    def get(self):
        """Get list of logs with filtering and pagination"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            filters = {}
            if request.args.get('level'):
                filters['level'] = request.args.get('level')
            if request.args.get('source'):
                filters['source'] = request.args.get('source')
            if request.args.get('server_alias'):
                filters['server_alias'] = request.args.get('server_alias')
            if request.args.get('deploy_id'):
                filters['deploy_id'] = request.args.get('deploy_id', type=int)
            if request.args.get('start_date'):
                filters['start_date'] = request.args.get('start_date')
            if request.args.get('end_date'):
                filters['end_date'] = request.args.get('end_date')
            
            result = LogService.get_logs(
                page=page,
                per_page=per_page,
                **filters
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting logs: {str(e)}")
            logs_ns.abort(500, f"Error getting logs: {str(e)}")

@logs_ns.route('/stats')
class LogStats(Resource):
    @logs_ns.doc('get_log_stats')
    @logs_ns.marshal_with(log_stats_model)
    @jwt_required()
    def get(self):
        """Get log statistics"""
        try:
            result = LogService.get_log_stats()
            return result
            
        except Exception as e:
            logger.error(f"Error getting log stats: {str(e)}")
            logs_ns.abort(500, f"Error getting log stats: {str(e)}")

@logs_ns.route('/download')
class LogDownload(Resource):
    @logs_ns.doc('download_logs')
    @logs_ns.param('format', 'Download format (csv, json)', type=str, default='csv')
    @logs_ns.param('level', 'Filter by log level', type=str)
    @logs_ns.param('source', 'Filter by log source', type=str)
    @logs_ns.param('start_date', 'Filter from date (ISO format)', type=str)
    @logs_ns.param('end_date', 'Filter to date (ISO format)', type=str)
    @jwt_required()
    def get(self):
        """Download logs in specified format"""
        try:
            format_type = request.args.get('format', 'csv')
            
            filters = {}
            if request.args.get('level'):
                filters['level'] = request.args.get('level')
            if request.args.get('source'):
                filters['source'] = request.args.get('source')
            if request.args.get('start_date'):
                filters['start_date'] = request.args.get('start_date')
            if request.args.get('end_date'):
                filters['end_date'] = request.args.get('end_date')
            
            result = LogService.export_logs(format_type, **filters)
            return result
            
        except Exception as e:
            logger.error(f"Error downloading logs: {str(e)}")
            logs_ns.abort(500, f"Error downloading logs: {str(e)}")

@logs_ns.route('/deployment/<int:deploy_id>')
class DeploymentLogs(Resource):
    @logs_ns.doc('get_deployment_logs')
    @logs_ns.marshal_with(log_list_model)
    @jwt_required()
    def get(self, deploy_id):
        """Get logs for specific deployment"""
        try:
            result = LogService.get_deployment_logs(deploy_id)
            return result
            
        except Exception as e:
            logger.error(f"Error getting deployment logs {deploy_id}: {str(e)}")
            logs_ns.abort(500, f"Error getting deployment logs: {str(e)}")

@logs_ns.route('/server/<string:server_alias>')
class ServerLogs(Resource):
    @logs_ns.doc('get_server_logs')
    @logs_ns.marshal_with(log_list_model)
    @logs_ns.param('page', 'Page number', type=int, default=1)
    @logs_ns.param('per_page', 'Items per page', type=int, default=20)
    @jwt_required()
    def get(self, server_alias):
        """Get logs for specific server"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            result = LogService.get_server_logs(
                server_alias=server_alias,
                page=page,
                per_page=per_page
            )
            return result
            
        except Exception as e:
            logger.error(f"Error getting server logs {server_alias}: {str(e)}")
            logs_ns.abort(500, f"Error getting server logs: {str(e)}")
