"""
Health metric model for server monitoring
"""
from datetime import datetime, timezone
from . import db

class HealthMetric(db.Model):
    __tablename__ = 'health_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False, index=True)
    
    # Health metrics
    ping_time = db.Column(db.Float, nullable=True)  # Ping response time in ms
    cpu_usage = db.Column(db.Float, nullable=True)  # CPU usage percentage
    memory_usage = db.Column(db.Float, nullable=True)  # Memory usage percentage
    disk_usage = db.Column(db.Float, nullable=True)  # Disk usage percentage
    
    # Network metrics
    network_rx = db.Column(db.BigInteger, nullable=True)  # Network bytes received
    network_tx = db.Column(db.BigInteger, nullable=True)  # Network bytes transmitted
    
    # System information
    uptime = db.Column(db.Integer, nullable=True)  # System uptime in seconds
    load_average = db.Column(db.Float, nullable=True)  # System load average
    
    # Status
    status = db.Column(db.String(20), default='healthy', nullable=False)  # healthy, warning, critical, unknown
    dns_resolved = db.Column(db.String(255), nullable=True)  # Resolved DNS name
    
    # Error information
    error_message = db.Column(db.Text, nullable=True)
    check_type = db.Column(db.String(50), default='automatic')  # automatic, manual
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def determine_status(self):
        """Automatically determine health status based on metrics"""
        if self.error_message:
            return 'critical'
        
        # Define thresholds
        cpu_warning_threshold = 80.0
        cpu_critical_threshold = 95.0
        memory_warning_threshold = 85.0
        memory_critical_threshold = 95.0
        disk_warning_threshold = 85.0
        disk_critical_threshold = 95.0
        ping_warning_threshold = 200.0  # ms
        ping_critical_threshold = 1000.0  # ms
        
        # Check for critical conditions
        if (self.cpu_usage and self.cpu_usage > cpu_critical_threshold) or \
           (self.memory_usage and self.memory_usage > memory_critical_threshold) or \
           (self.disk_usage and self.disk_usage > disk_critical_threshold) or \
           (self.ping_time and self.ping_time > ping_critical_threshold):
            return 'critical'
        
        # Check for warning conditions
        if (self.cpu_usage and self.cpu_usage > cpu_warning_threshold) or \
           (self.memory_usage and self.memory_usage > memory_warning_threshold) or \
           (self.disk_usage and self.disk_usage > disk_warning_threshold) or \
           (self.ping_time and self.ping_time > ping_warning_threshold):
            return 'warning'
        
        return 'healthy'
    
    def update_status(self):
        """Update status based on current metrics"""
        self.status = self.determine_status()
        self.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def is_healthy(self):
        """Check if server is healthy"""
        return self.status == 'healthy'
    
    def is_warning(self):
        """Check if server has warnings"""
        return self.status == 'warning'
    
    def is_critical(self):
        """Check if server is in critical state"""
        return self.status == 'critical'
    
    def get_uptime_formatted(self):
        """Get formatted uptime string"""
        if not self.uptime:
            return 'N/A'
        
        days = self.uptime // 86400
        hours = (self.uptime % 86400) // 3600
        minutes = (self.uptime % 3600) // 60
        
        if days > 0:
            return f'{days}d {hours}h {minutes}m'
        elif hours > 0:
            return f'{hours}h {minutes}m'
        else:
            return f'{minutes}m'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'ping_time': self.ping_time,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_rx': self.network_rx,
            'network_tx': self.network_tx,
            'uptime': self.uptime,
            'uptime_formatted': self.get_uptime_formatted(),
            'load_average': self.load_average,
            'status': self.status,
            'dns_resolved': self.dns_resolved,
            'error_message': self.error_message,
            'check_type': self.check_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_latest_metrics(cls, server_id=None, limit=100):
        """Get latest health metrics"""
        query = cls.query
        
        if server_id:
            query = query.filter_by(server_id=server_id)
            
        return query.order_by(db.desc(cls.created_at)).limit(limit).all()
    
    @classmethod
    def get_server_health_summary(cls, server_id, hours=24):
        """Get health summary for a server"""
        from sqlalchemy import func
        from datetime import timedelta
        
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        metrics = cls.query.filter(
            cls.server_id == server_id,
            cls.created_at >= since_time
        ).all()
        
        if not metrics:
            return None
        
        # Calculate averages
        total_metrics = len(metrics)
        avg_cpu = sum(m.cpu_usage for m in metrics if m.cpu_usage) / len([m for m in metrics if m.cpu_usage]) if any(m.cpu_usage for m in metrics) else None
        avg_memory = sum(m.memory_usage for m in metrics if m.memory_usage) / len([m for m in metrics if m.memory_usage]) if any(m.memory_usage for m in metrics) else None
        avg_disk = sum(m.disk_usage for m in metrics if m.disk_usage) / len([m for m in metrics if m.disk_usage]) if any(m.disk_usage for m in metrics) else None
        avg_ping = sum(m.ping_time for m in metrics if m.ping_time) / len([m for m in metrics if m.ping_time]) if any(m.ping_time for m in metrics) else None
        
        # Count status occurrences
        status_counts = {}
        for metric in metrics:
            status = metric.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_checks': total_metrics,
            'avg_cpu_usage': round(avg_cpu, 2) if avg_cpu else None,
            'avg_memory_usage': round(avg_memory, 2) if avg_memory else None,
            'avg_disk_usage': round(avg_disk, 2) if avg_disk else None,
            'avg_ping_time': round(avg_ping, 2) if avg_ping else None,
            'status_distribution': status_counts,
            'latest_metric': metrics[0].to_dict() if metrics else None
        }
    
    @classmethod
    def create_health_metric(cls, server_id, **kwargs):
        """Create new health metric"""
        metric = cls(server_id=server_id, **kwargs)
        metric.status = metric.determine_status()
        db.session.add(metric)
        db.session.commit()
        return metric
    
    def __repr__(self):
        return f'<HealthMetric {self.id} - Server {self.server_id} - {self.status}>'
