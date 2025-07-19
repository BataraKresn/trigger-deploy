"""
Deploy log model for tracking deployment history
"""
from datetime import datetime, timezone, timedelta
from . import db

class DeployLog(db.Model):
    __tablename__ = 'deploy_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False, index=True)
    executed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
    # Deployment details
    status = db.Column(db.String(20), nullable=False, index=True)  # running, success, error, cancelled
    command = db.Column(db.Text, nullable=True)
    
    # Logs and output
    output = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Timing
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # Duration in seconds
    
    # Metadata
    deployment_type = db.Column(db.String(50), default='manual')  # manual, automated, scheduled
    git_commit = db.Column(db.String(40), nullable=True)  # Git commit hash if applicable
    environment = db.Column(db.String(50), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def complete_deployment(self, status, output=None, error_message=None):
        """Mark deployment as completed"""
        self.status = status
        self.completed_at = datetime.now(timezone.utc)
        self.duration = int((self.completed_at - self.started_at).total_seconds())
        
        if output:
            self.output = output
        if error_message:
            self.error_message = error_message
            
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def update_output(self, output, append=True):
        """Update deployment output"""
        if append and self.output:
            self.output += '\n' + output
        else:
            self.output = output
        
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def is_running(self):
        """Check if deployment is still running"""
        return self.status == 'running'
    
    def is_successful(self):
        """Check if deployment was successful"""
        return self.status == 'success'
    
    def is_failed(self):
        """Check if deployment failed"""
        return self.status == 'error'
    
    def get_duration_formatted(self):
        """Get formatted duration string"""
        if not self.duration:
            return 'N/A'
        
        if self.duration < 60:
            return f'{self.duration}s'
        elif self.duration < 3600:
            minutes = self.duration // 60
            seconds = self.duration % 60
            return f'{minutes}m {seconds}s'
        else:
            hours = self.duration // 3600
            minutes = (self.duration % 3600) // 60
            return f'{hours}h {minutes}m'
    
    def to_dict(self, include_output=True):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'server_id': self.server_id,
            'executed_by': self.executed_by,
            'status': self.status,
            'command': self.command,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration,
            'duration_formatted': self.get_duration_formatted(),
            'deployment_type': self.deployment_type,
            'git_commit': self.git_commit,
            'environment': self.environment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_output:
            data['output'] = self.output
            data['error_message'] = self.error_message
            
        # Include related data
        if hasattr(self, 'server') and self.server:
            data['server'] = {
                'id': self.server.id,
                'alias': self.server.alias,
                'name': self.server.name,
                'ip': self.server.ip
            }
            
        if hasattr(self, 'executed_by_user') and self.executed_by_user:
            data['executed_by_user'] = {
                'id': self.executed_by_user.id,
                'username': self.executed_by_user.username
            }
            
        return data
    
    @classmethod
    def get_recent_logs(cls, limit=50, server_id=None, status=None):
        """Get recent deployment logs with optional filters"""
        query = cls.query
        
        if server_id:
            query = query.filter_by(server_id=server_id)
        if status:
            query = query.filter_by(status=status)
            
        return query.order_by(db.desc(cls.created_at)).limit(limit).all()
    
    @classmethod
    def get_deployment_stats(cls, server_id=None, days=30):
        """Get deployment statistics"""
        from sqlalchemy import func
        
        query = cls.query
        if server_id:
            query = query.filter_by(server_id=server_id)
            
        # Filter by date range
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(cls.created_at >= since_date)
        
        total = query.count()
        successful = query.filter_by(status='success').count()
        failed = query.filter_by(status='error').count()
        running = query.filter_by(status='running').count()
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'running': running,
            'success_rate': (successful / total * 100) if total > 0 else 0
        }
    
    @classmethod
    def create_deployment_log(cls, server_id, executed_by=None, command=None, **kwargs):
        """Create new deployment log"""
        log = cls(
            server_id=server_id,
            executed_by=executed_by,
            command=command,
            status='running',
            **kwargs
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    def __repr__(self):
        return f'<DeployLog {self.id} - {self.server.alias if hasattr(self, "server") else self.server_id} - {self.status}>'
