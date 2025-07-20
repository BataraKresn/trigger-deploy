# =================================
# Server and Service Models
# =================================

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


@dataclass
class Server:
    """Server configuration model"""
    name: str
    ip: str
    user: str
    description: str
    alias: str
    path: str
    type: str
    port: int = 22
    status: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Server':
        """Create Server instance from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Server to dictionary"""
        return {
            'name': self.name,
            'ip': self.ip,
            'user': self.user,
            'description': self.description,
            'alias': self.alias,
            'path': self.path,
            'type': self.type,
            'port': self.port,
            'status': self.status
        }


@dataclass
class Service:
    """Service configuration model"""
    name: str
    url: str
    check_interval: int = 300
    timeout: int = 10
    status: Optional[str] = None
    last_check: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Service':
        """Create Service instance from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Service to dictionary"""
        return {
            'name': self.name,
            'url': self.url,
            'check_interval': self.check_interval,
            'timeout': self.timeout,
            'status': self.status,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }


@dataclass
class Deployment:
    """Deployment record model"""
    deployment_id: str
    server_name: str
    server_ip: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    duration: Optional[float]
    client_ip: str
    log_file: Optional[str]
    error_message: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Deployment':
        """Create Deployment instance from dictionary"""
        started_at = data['started_at']
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        
        completed_at = data.get('completed_at')
        if completed_at and isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        
        return cls(
            deployment_id=data['deployment_id'],
            server_name=data['server_name'],
            server_ip=data['server_ip'],
            started_at=started_at,
            completed_at=completed_at,
            status=data['status'],
            duration=data.get('duration'),
            client_ip=data['client_ip'],
            log_file=data.get('log_file'),
            error_message=data.get('error_message')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Deployment to dictionary"""
        return {
            'deployment_id': self.deployment_id,
            'server_name': self.server_name,
            'server_ip': self.server_ip,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status,
            'duration': self.duration,
            'client_ip': self.client_ip,
            'log_file': self.log_file,
            'error_message': self.error_message
        }
