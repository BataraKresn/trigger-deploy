"""
Configuration Management System
Advanced configuration management with validation, versioning, and rollback capabilities
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import hashlib
from src.models.database import get_db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConfigVersion:
    """Configuration version information"""
    version_id: str
    timestamp: datetime
    author: str
    description: str
    config_hash: str
    config_data: Dict[str, Any]
    is_active: bool = False

@dataclass
class ConfigValidationResult:
    """Configuration validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

class ConfigurationManager:
    """Advanced configuration management system"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.config_dir = Path('/workspaces/trigger-deploy/config')
        self.backup_dir = Path('/workspaces/trigger-deploy/config/backups')
        self.schema_dir = Path('/workspaces/trigger-deploy/config/schemas')
        
        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        self.schema_dir.mkdir(exist_ok=True)
        
        # Configuration schemas for validation
        self.config_schemas = {
            'servers': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'required': ['name', 'alias', 'host', 'port'],
                    'properties': {
                        'name': {'type': 'string', 'minLength': 1},
                        'alias': {'type': 'string', 'minLength': 1},
                        'host': {'type': 'string', 'minLength': 1},
                        'port': {'type': 'integer', 'minimum': 1, 'maximum': 65535},
                        'user': {'type': 'string'},
                        'key_path': {'type': 'string'},
                        'environment': {'type': 'string', 'enum': ['production', 'staging', 'development']},
                        'enabled': {'type': 'boolean'},
                        'tags': {'type': 'array', 'items': {'type': 'string'}}
                    }
                }
            },
            'services': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'required': ['name', 'url'],
                    'properties': {
                        'name': {'type': 'string', 'minLength': 1},
                        'url': {'type': 'string', 'format': 'uri'},
                        'method': {'type': 'string', 'enum': ['GET', 'POST', 'PUT', 'DELETE']},
                        'timeout': {'type': 'integer', 'minimum': 1, 'maximum': 300},
                        'enabled': {'type': 'boolean'},
                        'expected_status': {'type': 'integer', 'minimum': 100, 'maximum': 599},
                        'headers': {'type': 'object'},
                        'check_interval': {'type': 'integer', 'minimum': 10}
                    }
                }
            },
            'application': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'version': {'type': 'string'},
                    'environment': {'type': 'string', 'enum': ['production', 'staging', 'development']},
                    'debug': {'type': 'boolean'},
                    'secret_key': {'type': 'string', 'minLength': 32},
                    'database': {
                        'type': 'object',
                        'properties': {
                            'url': {'type': 'string'},
                            'pool_size': {'type': 'integer', 'minimum': 1, 'maximum': 100},
                            'max_overflow': {'type': 'integer', 'minimum': 0, 'maximum': 100},
                            'timeout': {'type': 'integer', 'minimum': 1, 'maximum': 300}
                        }
                    },
                    'email': {
                        'type': 'object',
                        'properties': {
                            'smtp_server': {'type': 'string'},
                            'smtp_port': {'type': 'integer', 'minimum': 1, 'maximum': 65535},
                            'username': {'type': 'string'},
                            'password': {'type': 'string'},
                            'use_tls': {'type': 'boolean'},
                            'from_name': {'type': 'string'},
                            'from_email': {'type': 'string', 'format': 'email'}
                        }
                    }
                }
            }
        }
    
    async def initialize_config_tables(self):
        """Initialize database tables for configuration management"""
        try:
            conn = await self.db_manager.get_connection()
            
            # Configuration versions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS config_versions (
                    id SERIAL PRIMARY KEY,
                    version_id VARCHAR(50) NOT NULL UNIQUE,
                    config_type VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    author VARCHAR(100) NOT NULL,
                    description TEXT,
                    config_hash VARCHAR(64) NOT NULL,
                    config_data JSONB NOT NULL,
                    is_active BOOLEAN DEFAULT FALSE,
                    INDEX(config_type, timestamp),
                    INDEX(version_id),
                    INDEX(is_active)
                )
            """)
            
            # Configuration change log
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS config_change_log (
                    id SERIAL PRIMARY KEY,
                    config_type VARCHAR(50) NOT NULL,
                    action VARCHAR(20) NOT NULL,
                    old_version_id VARCHAR(50),
                    new_version_id VARCHAR(50),
                    author VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    changes_summary TEXT,
                    rollback_available BOOLEAN DEFAULT TRUE,
                    INDEX(config_type, timestamp),
                    INDEX(action)
                )
            """)
            
            # Configuration templates
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS config_templates (
                    id SERIAL PRIMARY KEY,
                    template_name VARCHAR(100) NOT NULL UNIQUE,
                    config_type VARCHAR(50) NOT NULL,
                    template_data JSONB NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_default BOOLEAN DEFAULT FALSE,
                    INDEX(config_type),
                    INDEX(template_name)
                )
            """)
            
            await conn.close()
            logger.info("Configuration management tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize config tables: {e}")
            raise
    
    def calculate_config_hash(self, config_data: Dict[str, Any]) -> str:
        """Calculate hash for configuration data"""
        config_str = json.dumps(config_data, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def validate_config(self, config_type: str, config_data: Dict[str, Any]) -> ConfigValidationResult:
        """Validate configuration data against schema"""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            schema = self.config_schemas.get(config_type)
            if not schema:
                errors.append(f"No schema found for config type: {config_type}")
                return ConfigValidationResult(False, errors, warnings, suggestions)
            
            # Basic validation (simplified - would use jsonschema in real implementation)
            if config_type == 'servers':
                if not isinstance(config_data, list):
                    errors.append("Servers config must be an array")
                else:
                    for i, server in enumerate(config_data):
                        if not isinstance(server, dict):
                            errors.append(f"Server {i} must be an object")
                            continue
                        
                        # Check required fields
                        required_fields = ['name', 'alias', 'host', 'port']
                        for field in required_fields:
                            if field not in server:
                                errors.append(f"Server {i}: Missing required field '{field}'")
                        
                        # Check port range
                        if 'port' in server:
                            port = server['port']
                            if not isinstance(port, int) or port < 1 or port > 65535:
                                errors.append(f"Server {i}: Port must be integer between 1-65535")
                        
                        # Check environment
                        if 'environment' in server:
                            env = server['environment']
                            valid_envs = ['production', 'staging', 'development']
                            if env not in valid_envs:
                                warnings.append(f"Server {i}: Unknown environment '{env}'. Valid: {valid_envs}")
                        
                        # Suggestions
                        if 'tags' not in server:
                            suggestions.append(f"Server {i}: Consider adding 'tags' for better organization")
            
            elif config_type == 'services':
                if not isinstance(config_data, list):
                    errors.append("Services config must be an array")
                else:
                    for i, service in enumerate(config_data):
                        if not isinstance(service, dict):
                            errors.append(f"Service {i} must be an object")
                            continue
                        
                        # Check required fields
                        required_fields = ['name', 'url']
                        for field in required_fields:
                            if field not in service:
                                errors.append(f"Service {i}: Missing required field '{field}'")
                        
                        # Check URL format (basic)
                        if 'url' in service:
                            url = service['url']
                            if not url.startswith(('http://', 'https://')):
                                errors.append(f"Service {i}: URL must start with http:// or https://")
                        
                        # Check timeout
                        if 'timeout' in service:
                            timeout = service['timeout']
                            if not isinstance(timeout, int) or timeout < 1 or timeout > 300:
                                warnings.append(f"Service {i}: Timeout should be between 1-300 seconds")
            
            # General suggestions
            if not errors and not warnings:
                suggestions.append("Configuration looks good! Consider adding comments for complex settings.")
            
            is_valid = len(errors) == 0
            return ConfigValidationResult(is_valid, errors, warnings, suggestions)
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return ConfigValidationResult(False, errors, warnings, suggestions)
    
    async def save_config_version(self, config_type: str, config_data: Dict[str, Any], 
                                author: str, description: str = "") -> str:
        """Save a new configuration version"""
        try:
            # Generate version ID
            timestamp = datetime.now()
            version_id = f"{config_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Calculate hash
            config_hash = self.calculate_config_hash(config_data)
            
            # Validate configuration
            validation = self.validate_config(config_type, config_data)
            if not validation.is_valid:
                raise ValueError(f"Configuration validation failed: {validation.errors}")
            
            conn = await self.db_manager.get_connection()
            
            # Deactivate current active version
            await conn.execute("""
                UPDATE config_versions 
                SET is_active = FALSE 
                WHERE config_type = $1 AND is_active = TRUE
            """, config_type)
            
            # Insert new version
            await conn.execute("""
                INSERT INTO config_versions 
                (version_id, config_type, timestamp, author, description, config_hash, config_data, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE)
            """, version_id, config_type, timestamp, author, description, 
            config_hash, json.dumps(config_data))
            
            # Log the change
            await conn.execute("""
                INSERT INTO config_change_log 
                (config_type, action, new_version_id, author, changes_summary)
                VALUES ($1, 'create', $2, $3, $4)
            """, config_type, version_id, author, f"Created new configuration version")
            
            await conn.close()
            
            # Save to file system
            await self.save_config_to_file(config_type, config_data, version_id)
            
            logger.info(f"Saved configuration version {version_id} for {config_type}")
            return version_id
            
        except Exception as e:
            logger.error(f"Failed to save config version: {e}")
            raise
    
    async def save_config_to_file(self, config_type: str, config_data: Dict[str, Any], version_id: str):
        """Save configuration to file system"""
        try:
            # Save current config
            config_file = self.config_dir / f"{config_type}.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            # Save backup
            backup_file = self.backup_dir / f"{config_type}_{version_id}.json"
            with open(backup_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Failed to save config to file: {e}")
            raise
    
    async def get_config_version(self, config_type: str, version_id: str = None) -> Optional[ConfigVersion]:
        """Get a specific configuration version"""
        try:
            conn = await self.db_manager.get_connection()
            
            if version_id:
                query = """
                    SELECT * FROM config_versions 
                    WHERE config_type = $1 AND version_id = $2
                """
                row = await conn.fetchrow(query, config_type, version_id)
            else:
                query = """
                    SELECT * FROM config_versions 
                    WHERE config_type = $1 AND is_active = TRUE
                """
                row = await conn.fetchrow(query, config_type)
            
            await conn.close()
            
            if row:
                config_data = json.loads(row['config_data']) if isinstance(row['config_data'], str) else row['config_data']
                return ConfigVersion(
                    version_id=row['version_id'],
                    timestamp=row['timestamp'],
                    author=row['author'],
                    description=row['description'] or "",
                    config_hash=row['config_hash'],
                    config_data=config_data,
                    is_active=row['is_active']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get config version: {e}")
            return None
    
    async def list_config_versions(self, config_type: str, limit: int = 50) -> List[ConfigVersion]:
        """List configuration versions"""
        try:
            conn = await self.db_manager.get_connection()
            
            query = """
                SELECT * FROM config_versions 
                WHERE config_type = $1 
                ORDER BY timestamp DESC 
                LIMIT $2
            """
            rows = await conn.fetch(query, config_type, limit)
            await conn.close()
            
            versions = []
            for row in rows:
                config_data = json.loads(row['config_data']) if isinstance(row['config_data'], str) else row['config_data']
                versions.append(ConfigVersion(
                    version_id=row['version_id'],
                    timestamp=row['timestamp'],
                    author=row['author'],
                    description=row['description'] or "",
                    config_hash=row['config_hash'],
                    config_data=config_data,
                    is_active=row['is_active']
                ))
            
            return versions
            
        except Exception as e:
            logger.error(f"Failed to list config versions: {e}")
            return []
    
    async def rollback_config(self, config_type: str, target_version_id: str, author: str) -> bool:
        """Rollback configuration to a previous version"""
        try:
            # Get target version
            target_version = await self.get_config_version(config_type, target_version_id)
            if not target_version:
                raise ValueError(f"Version {target_version_id} not found")
            
            # Get current version for logging
            current_version = await self.get_config_version(config_type)
            
            conn = await self.db_manager.get_connection()
            
            # Deactivate current version
            await conn.execute("""
                UPDATE config_versions 
                SET is_active = FALSE 
                WHERE config_type = $1 AND is_active = TRUE
            """, config_type)
            
            # Activate target version
            await conn.execute("""
                UPDATE config_versions 
                SET is_active = TRUE 
                WHERE version_id = $1
            """, target_version_id)
            
            # Log the rollback
            await conn.execute("""
                INSERT INTO config_change_log 
                (config_type, action, old_version_id, new_version_id, author, changes_summary)
                VALUES ($1, 'rollback', $2, $3, $4, $5)
            """, config_type, 
            current_version.version_id if current_version else None,
            target_version_id, author, 
            f"Rolled back to version {target_version_id}")
            
            await conn.close()
            
            # Update file system
            await self.save_config_to_file(config_type, target_version.config_data, target_version_id)
            
            logger.info(f"Rolled back {config_type} to version {target_version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback config: {e}")
            return False
    
    async def get_config_diff(self, config_type: str, version1_id: str, version2_id: str) -> Dict[str, Any]:
        """Get differences between two configuration versions"""
        try:
            version1 = await self.get_config_version(config_type, version1_id)
            version2 = await self.get_config_version(config_type, version2_id)
            
            if not version1 or not version2:
                return {'error': 'One or both versions not found'}
            
            # Simple diff implementation
            # In a real implementation, you'd use a proper diff library
            
            changes = {
                'version1': {
                    'id': version1.version_id,
                    'timestamp': version1.timestamp.isoformat(),
                    'author': version1.author
                },
                'version2': {
                    'id': version2.version_id,
                    'timestamp': version2.timestamp.isoformat(),
                    'author': version2.author
                },
                'summary': 'Configuration comparison (detailed diff would require diff library)',
                'has_changes': version1.config_hash != version2.config_hash
            }
            
            return changes
            
        except Exception as e:
            logger.error(f"Failed to get config diff: {e}")
            return {'error': str(e)}
    
    async def export_config(self, config_type: str, version_id: str = None) -> Dict[str, Any]:
        """Export configuration for backup or transfer"""
        try:
            version = await self.get_config_version(config_type, version_id)
            if not version:
                return {'error': 'Configuration version not found'}
            
            export_data = {
                'export_info': {
                    'exported_at': datetime.now().isoformat(),
                    'config_type': config_type,
                    'version_id': version.version_id,
                    'original_timestamp': version.timestamp.isoformat(),
                    'original_author': version.author,
                    'description': version.description
                },
                'configuration': version.config_data,
                'metadata': {
                    'hash': version.config_hash,
                    'schema_version': '1.0'
                }
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            return {'error': str(e)}

# Global instance
config_manager = ConfigurationManager()
