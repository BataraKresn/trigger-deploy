"""
Backend Routes Module

This module initializes and registers all API routes/namespaces for the Deploy Server backend.
It provides a centralized way to configure all API endpoints with Flask-RESTX.
"""

from .server import server_ns
from .deploy import deploy_ns
from .health import health_ns
from .logs import logs_ns
from .auth import auth_ns

def register_namespaces(api):
    """
    Register all namespaces with the Flask-RESTX API instance.
    
    Args:
        api: Flask-RESTX API instance
    """
    # Authentication routes
    api.add_namespace(auth_ns, path='/auth')
    
    # Server management routes
    api.add_namespace(server_ns, path='/servers')
    
    # Deployment routes
    api.add_namespace(deploy_ns, path='/deploy')
    
    # Health check routes
    api.add_namespace(health_ns, path='/health')
    
    # Logging routes
    api.add_namespace(logs_ns, path='/logs')

# Export all namespaces for individual import if needed
__all__ = [
    'register_namespaces',
    'server_ns',
    'deploy_ns', 
    'health_ns',
    'logs_ns',
    'auth_ns'
]
