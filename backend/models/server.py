"""
Server model for managing deployment targets
"""
from datetime import datetime, timezone
from . import db

class Server(db.Model):
    __tablename__ = 'servers'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Server identification
    ip = db.Column(db.String(45), nullable=False, index=True)  # Support IPv4 and IPv6
    alias = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    
    # SSH connection details
    user = db.Column(db.String(100), nullable=False)
    script_path = db.Column(db.String(500), nullable=False)
    ssh_port = db.Column(db.Integer, default=22, nullable=False)
    
    # Server metadata
    description = db.Column(db.Text, nullable=True)
    environment = db.Column(db.String(50), default='production')  # production, staging, development
    
    # Server status
    status = db.Column(db.String(20), default='unknown', nullable=False)  # online, offline, deploying, error
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_deployed = db.Column(db.DateTime, nullable=True)
    last_health_check = db.Column(db.DateTime, nullable=True)
    
    # Foreign key
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    deploy_logs = db.relationship('DeployLog', backref='server', lazy='dynamic', cascade='all, delete-orphan')
    health_metrics = db.relationship('HealthMetric', backref='server', lazy='dynamic', cascade='all, delete-orphan')
    creator = db.relationship('User', backref='created_servers')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('ip', 'ssh_port', name='unique_server_endpoint'),
        db.UniqueConstraint('alias', name='unique_server_alias'),
    )
    
    def update_status(self, status):
        """Update server status"""
        self.status = status
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def update_last_deployed(self):
        """Update last deployed timestamp"""
        self.last_deployed = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def update_last_health_check(self):
        """Update last health check timestamp"""
        self.last_health_check = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def get_recent_deploys(self, limit=10):
        """Get recent deployment logs"""
        return self.deploy_logs.order_by(
            db.desc('created_at')
        ).limit(limit).all()
    
    def get_latest_health_metric(self):
        """Get latest health metric"""
        return self.health_metrics.order_by(
            db.desc('created_at')
        ).first()
    
    def is_online(self):
        """Check if server is online"""
        return self.status == 'online'
    
    def is_deploying(self):
        """Check if server is currently deploying"""
        return self.status == 'deploying'
    
    def to_dict(self, include_relations=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'ip': self.ip,
            'alias': self.alias,
            'name': self.name,
            'user': self.user,
            'script_path': self.script_path,
            'ssh_port': self.ssh_port,
            'description': self.description,
            'environment': self.environment,
            'status': self.status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_deployed': self.last_deployed.isoformat() if self.last_deployed else None,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'created_by': self.created_by,
        }
        
        if include_relations:
            data['recent_deploys'] = [deploy.to_dict() for deploy in self.get_recent_deploys(5)]
            latest_health = self.get_latest_health_metric()
            data['latest_health'] = latest_health.to_dict() if latest_health else None
            
        return data
    
    @classmethod
    def find_by_ip(cls, ip, port=22):
        """Find server by IP and port"""
        return cls.query.filter_by(ip=ip, ssh_port=port).first()
    
    @classmethod
    def find_by_alias(cls, alias):
        """Find server by alias"""
        return cls.query.filter_by(alias=alias).first()
    
    @classmethod
    def get_active_servers(cls):
        """Get all active servers"""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def create_server(cls, ip, alias, name, user, script_path, **kwargs):
        """Create new server"""
        server = cls(
            ip=ip,
            alias=alias,
            name=name,
            user=user,
            script_path=script_path,
            **kwargs
        )
        db.session.add(server)
        db.session.commit()
        return server
    
    def __repr__(self):
        return f'<Server {self.alias} ({self.ip})>'
