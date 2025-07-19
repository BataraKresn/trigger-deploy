from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.deploy_service import DeployService
from schemas import DeployRequestSchema, DeployResponseSchema
from utils.rate_limit import limiter
import logging

logger = logging.getLogger(__name__)

# Create namespace
deploy_ns = Namespace('deploy', description='Deploy operations')

# API Models for documentation
deploy_request_model = deploy_ns.model('DeployRequest', {
    'server_alias': fields.String(required=True, description='Server alias to deploy to'),
    'environment': fields.String(required=False, description='Deployment environment'),
    'branch': fields.String(required=False, description='Git branch to deploy'),
    'tags': fields.List(fields.String, required=False, description='Deployment tags'),
    'variables': fields.Raw(required=False, description='Environment variables for deployment')
})

deploy_response_model = deploy_ns.model('DeployResponse', {
    'id': fields.Integer(description='Deploy log ID'),
    'status': fields.String(description='Deployment status'),
    'server_alias': fields.String(description='Server alias'),
    'output': fields.String(description='Deployment output'),
    'exit_code': fields.Integer(description='Deployment exit code'),
    'started_at': fields.DateTime(description='Deployment start time'),
    'finished_at': fields.DateTime(description='Deployment finish time'),
    'duration': fields.Float(description='Deployment duration in seconds')
})

deploy_list_model = deploy_ns.model('DeployList', {
    'deploys': fields.List(fields.Nested(deploy_response_model)),
    'total': fields.Integer(description='Total number of deployments'),
    'page': fields.Integer(description='Current page'),
    'per_page': fields.Integer(description='Items per page'),
    'pages': fields.Integer(description='Total pages')
})

deploy_stats_model = deploy_ns.model('DeployStats', {
    'total_deploys': fields.Integer(description='Total number of deployments'),
    'successful_deploys': fields.Integer(description='Number of successful deployments'),
    'failed_deploys': fields.Integer(description='Number of failed deployments'),
    'success_rate': fields.Float(description='Success rate percentage'),
    'avg_duration': fields.Float(description='Average deployment duration'),
    'recent_deploys': fields.List(fields.Nested(deploy_response_model), description='Recent deployments')
})

@deploy_ns.route('')
class DeployList(Resource):
    @deploy_ns.doc('list_deploys')
    @deploy_ns.marshal_with(deploy_list_model)
    @deploy_ns.param('page', 'Page number', type=int, default=1)
    @deploy_ns.param('per_page', 'Items per page', type=int, default=20)
    @deploy_ns.param('server_alias', 'Filter by server alias', type=str)
    @deploy_ns.param('status', 'Filter by status', type=str)
    @deploy_ns.param('environment', 'Filter by environment', type=str)
    @jwt_required()
    def get(self):
        """Get list of deployments with filtering and pagination"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            filters = {}
            if request.args.get('server_alias'):
                filters['server_alias'] = request.args.get('server_alias')
            if request.args.get('status'):
                filters['status'] = request.args.get('status')
            if request.args.get('environment'):
                filters['environment'] = request.args.get('environment')
            
            result = DeployService.get_deploy_logs(
                page=page,
                per_page=per_page,
                **filters
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting deploy list: {str(e)}")
            deploy_ns.abort(500, f"Error getting deploy list: {str(e)}")

    @deploy_ns.doc('create_deploy')
    @deploy_ns.expect(deploy_request_model)
    @deploy_ns.marshal_with(deploy_response_model, code=201)
    @limiter.limit("10 per minute")
    @jwt_required()
    def post(self):
        """Trigger a new deployment"""
        try:
            # Validate input
            schema = DeployRequestSchema()
            data = schema.load(request.json)
            
            # Get current user
            current_user_id = get_jwt_identity()
            
            # Start deployment
            result = DeployService.trigger_deployment(
                user_id=current_user_id,
                **data
            )
            
            return result, 201
            
        except Exception as e:
            logger.error(f"Error triggering deployment: {str(e)}")
            deploy_ns.abort(500, f"Error triggering deployment: {str(e)}")

@deploy_ns.route('/<int:deploy_id>')
class Deploy(Resource):
    @deploy_ns.doc('get_deploy')
    @deploy_ns.marshal_with(deploy_response_model)
    @jwt_required()
    def get(self, deploy_id):
        """Get specific deployment details"""
        try:
            result = DeployService.get_deploy_log(deploy_id)
            if not result:
                deploy_ns.abort(404, "Deployment not found")
            return result
            
        except Exception as e:
            logger.error(f"Error getting deployment {deploy_id}: {str(e)}")
            deploy_ns.abort(500, f"Error getting deployment: {str(e)}")

    @deploy_ns.doc('cancel_deploy')
    @jwt_required()
    def delete(self, deploy_id):
        """Cancel a running deployment"""
        try:
            current_user_id = get_jwt_identity()
            result = DeployService.cancel_deployment(deploy_id, current_user_id)
            
            if not result:
                deploy_ns.abort(404, "Deployment not found or cannot be cancelled")
            
            return {"message": "Deployment cancelled successfully"}
            
        except Exception as e:
            logger.error(f"Error cancelling deployment {deploy_id}: {str(e)}")
            deploy_ns.abort(500, f"Error cancelling deployment: {str(e)}")

@deploy_ns.route('/stats')
class DeployStats(Resource):
    @deploy_ns.doc('get_deploy_stats')
    @deploy_ns.marshal_with(deploy_stats_model)
    @jwt_required()
    def get(self):
        """Get deployment statistics"""
        try:
            result = DeployService.get_deployment_stats()
            return result
            
        except Exception as e:
            logger.error(f"Error getting deployment stats: {str(e)}")
            deploy_ns.abort(500, f"Error getting deployment stats: {str(e)}")

@deploy_ns.route('/<int:deploy_id>/output')
class DeployOutput(Resource):
    @deploy_ns.doc('get_deploy_output')
    @jwt_required()
    def get(self, deploy_id):
        """Get deployment output/logs"""
        try:
            result = DeployService.get_deploy_output(deploy_id)
            if not result:
                deploy_ns.abort(404, "Deployment not found")
            
            return {
                "output": result.get('output', ''),
                "exit_code": result.get('exit_code'),
                "status": result.get('status')
            }
            
        except Exception as e:
            logger.error(f"Error getting deployment output {deploy_id}: {str(e)}")
            deploy_ns.abort(500, f"Error getting deployment output: {str(e)}")
