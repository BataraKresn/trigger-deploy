# =================================
# Unit Tests for Trigger Deploy Server
# =================================

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

# Set test environment variables
os.environ['DEPLOY_TOKEN'] = 'test_token_123'
os.environ['LOG_DIR'] = 'test_logs'
os.environ['SERVERS_FILE'] = 'test_servers.json'

from src.models.config import config
from src.utils.helpers import validate_token, check_server_health
from src.models.entities import Server, Deployment


class TestConfig(unittest.TestCase):
    """Test configuration management"""
    
    def test_config_loading(self):
        """Test configuration loading"""
        self.assertEqual(config.TOKEN, 'test_token_123')
        self.assertEqual(config.LOG_DIR, 'test_logs')


class TestHelpers(unittest.TestCase):
    """Test helper functions"""
    
    def test_validate_token_valid(self):
        """Test token validation with valid token"""
        self.assertTrue(validate_token('test_token_123'))
    
    def test_validate_token_invalid(self):
        """Test token validation with invalid token"""
        self.assertFalse(validate_token('wrong_token'))
        self.assertFalse(validate_token(''))
        self.assertFalse(validate_token(None))
    
    @patch('subprocess.run')
    @patch('socket.socket')
    def test_check_server_health_online(self, mock_socket, mock_subprocess):
        """Test server health check for online server"""
        # Mock successful ping
        mock_subprocess.return_value.returncode = 0
        
        # Mock successful socket connection
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect_ex.return_value = 0
        mock_socket.return_value = mock_socket_instance
        
        result = check_server_health('127.0.0.1')
        self.assertEqual(result, 'online')
    
    @patch('subprocess.run')
    def test_check_server_health_offline(self, mock_subprocess):
        """Test server health check for offline server"""
        # Mock failed ping
        mock_subprocess.return_value.returncode = 1
        
        result = check_server_health('192.168.1.999')
        self.assertEqual(result, 'offline')


class TestModels(unittest.TestCase):
    """Test data models"""
    
    def test_server_model(self):
        """Test Server model"""
        server_data = {
            'name': 'Test Server',
            'ip': '127.0.0.1',
            'user': 'testuser',
            'description': 'Test description',
            'alias': 'test',
            'path': '/test/path',
            'type': 'Test Server',
            'port': 22
        }
        
        server = Server.from_dict(server_data)
        self.assertEqual(server.name, 'Test Server')
        self.assertEqual(server.ip, '127.0.0.1')
        self.assertEqual(server.port, 22)
        
        # Test to_dict conversion
        converted = server.to_dict()
        self.assertEqual(converted['name'], 'Test Server')
    
    def test_deployment_model(self):
        """Test Deployment model"""
        from datetime import datetime
        
        deployment_data = {
            'deployment_id': 'test-123',
            'server_name': 'Test Server',
            'server_ip': '127.0.0.1',
            'started_at': datetime.now(),
            'completed_at': None,
            'status': 'running',
            'duration': None,
            'client_ip': '192.168.1.1',
            'log_file': 'test.log'
        }
        
        deployment = Deployment(**deployment_data)
        self.assertEqual(deployment.deployment_id, 'test-123')
        self.assertEqual(deployment.status, 'running')


class TestAPI(unittest.TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        # Import app after setting environment variables
        from app import create_app
        self.app = create_app()
        self.client = self.app.test_client()
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_home_page(self):
        """Test home page"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    @patch('src.utils.helpers.validate_token')
    def test_trigger_invalid_token(self, mock_validate):
        """Test trigger endpoint with invalid token"""
        mock_validate.return_value = False
        
        response = self.client.post('/trigger', 
                                   json={'token': 'invalid', 'server': 'test'})
        self.assertEqual(response.status_code, 403)


if __name__ == '__main__':
    # Create test directories
    os.makedirs('test_logs', exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)
