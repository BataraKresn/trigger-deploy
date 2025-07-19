#!/usr/bin/env python3
"""
Basic tests for trigger-deploy application
Run with: python3 test_app.py
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, mock_open

# Add the current directory to sys.path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for testing
os.environ['DEPLOY_TOKEN'] = 'test_token_123'
os.environ['LOG_DIR'] = 'test_logs'

from app import app, is_valid_ip, validate_token, is_valid_server, Config

class TestTriggerDeploy(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Mock servers.json content
        self.test_servers = [
            {"ip": "192.168.1.100", "user": "admin", "name": "Server 1"},
            {"ip": "10.0.0.50", "user": "deploy", "name": "Server 2"}
        ]
    
    def test_config_initialization(self):
        """Test configuration initialization"""
        config = Config()
        self.assertEqual(config.TOKEN, 'test_token_123')
        self.assertEqual(config.LOG_DIR, 'test_logs')
    
    def test_is_valid_ip(self):
        """Test IP validation function"""
        # Valid IPs
        self.assertTrue(is_valid_ip('192.168.1.1'))
        self.assertTrue(is_valid_ip('10.0.0.1'))
        self.assertTrue(is_valid_ip('127.0.0.1'))
        
        # Invalid IPs
        self.assertFalse(is_valid_ip('300.300.300.300'))
        self.assertFalse(is_valid_ip('not.an.ip'))
        self.assertFalse(is_valid_ip(''))
        self.assertFalse(is_valid_ip('192.168.1'))
    
    def test_validate_token(self):
        """Test token validation"""
        self.assertTrue(validate_token('test_token_123'))
        self.assertFalse(validate_token('wrong_token'))
        self.assertFalse(validate_token(''))
        self.assertFalse(validate_token(None))
    
    @patch('builtins.open', mock_open(read_data='[{"ip": "192.168.1.100", "user": "admin"}]'))
    def test_is_valid_server(self):
        """Test server validation"""
        # This would require mocking the file read, simplified for now
        pass
    
    def test_home_endpoint(self):
        """Test home page"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('uptime_seconds', data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_trigger_invalid_token(self):
        """Test trigger endpoint with invalid token"""
        response = self.app.post('/trigger', 
                                json={'token': 'invalid_token'})
        self.assertEqual(response.status_code, 403)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_ping_method_not_allowed(self):
        """Test ping endpoint with GET method"""
        response = self.app.get('/ping')
        self.assertEqual(response.status_code, 405)
    
    def test_ping_missing_payload(self):
        """Test ping endpoint without JSON payload"""
        response = self.app.post('/ping')
        self.assertEqual(response.status_code, 400)
    
    def test_ping_invalid_ip(self):
        """Test ping endpoint with invalid IP"""
        response = self.app.post('/ping', 
                                json={'server': 'invalid.ip'})
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('Invalid IP format', data['message'])
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.app.get('/health?target=127.0.0.1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('target', data)
        self.assertIn('resolve', data)
        self.assertIn('ping', data)
    
    def test_logs_endpoint(self):
        """Test logs listing endpoint"""
        response = self.app.get('/logs')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

if __name__ == '__main__':
    print("🧪 Running basic tests for trigger-deploy application...")
    print("=" * 60)
    
    # Create test log directory
    os.makedirs('test_logs', exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)
    
    # Cleanup
    import shutil
    if os.path.exists('test_logs'):
        shutil.rmtree('test_logs')
