"""
Server Health Monitoring System
Enhanced server monitoring with health checks, performance metrics, and alerting
"""

import asyncio
import aiohttp
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import json
import os
from src.models.database import get_db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HealthMetric:
    """Individual health metric data"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    status: str  # 'healthy', 'warning', 'critical'
    threshold_warning: float = None
    threshold_critical: float = None

@dataclass
class ServerHealth:
    """Complete server health status"""
    server_name: str
    timestamp: datetime
    overall_status: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    response_time: float
    uptime: float
    active_connections: int
    load_average: List[float]
    temperature: Optional[float] = None

class ServerHealthMonitor:
    """Advanced server health monitoring system"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.monitoring_active = False
        self.check_interval = 30  # seconds
        self.health_thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0,
            'response_time_warning': 2000,  # ms
            'response_time_critical': 5000  # ms
        }
        
    async def initialize_monitoring_tables(self):
        """Initialize database tables for health monitoring"""
        try:
            conn = await self.db_manager.get_connection()
            
            # Server health metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS server_health_metrics (
                    id SERIAL PRIMARY KEY,
                    server_name VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metric_name VARCHAR(50) NOT NULL,
                    value NUMERIC(10,2) NOT NULL,
                    unit VARCHAR(20),
                    status VARCHAR(20) NOT NULL,
                    threshold_warning NUMERIC(10,2),
                    threshold_critical NUMERIC(10,2),
                    INDEX(server_name, timestamp),
                    INDEX(metric_name, timestamp)
                )
            """)
            
            # Server health summary table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS server_health_summary (
                    id SERIAL PRIMARY KEY,
                    server_name VARCHAR(100) NOT NULL UNIQUE,
                    last_check TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    overall_status VARCHAR(20) NOT NULL,
                    cpu_usage NUMERIC(5,2),
                    memory_usage NUMERIC(5,2),
                    disk_usage NUMERIC(5,2),
                    response_time NUMERIC(10,2),
                    uptime_hours NUMERIC(10,2),
                    active_connections INTEGER,
                    load_average JSONB,
                    network_io JSONB,
                    alerts_count INTEGER DEFAULT 0,
                    last_alert TIMESTAMP
                )
            """)
            
            # Health alerts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS health_alerts (
                    id SERIAL PRIMARY KEY,
                    server_name VARCHAR(100) NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL,
                    metric_value NUMERIC(10,2),
                    threshold_value NUMERIC(10,2),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    INDEX(server_name, created_at),
                    INDEX(severity, resolved)
                )
            """)
            
            await conn.close()
            logger.info("Health monitoring tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize monitoring tables: {e}")
            raise
    
    async def get_system_metrics(self, server_name: str = 'localhost') -> ServerHealth:
        """Get comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network metrics
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': float(network.bytes_sent),
                'bytes_recv': float(network.bytes_recv),
                'packets_sent': float(network.packets_sent),
                'packets_recv': float(network.packets_recv)
            }
            
            # Connection count
            try:
                active_connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                active_connections = 0
            
            # Uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time
            uptime_hours = uptime / 3600
            
            # Response time (self-ping)
            response_time = await self.measure_response_time(server_name)
            
            # Determine overall status
            overall_status = self.calculate_overall_status(
                cpu_usage, memory_usage, disk_usage, response_time
            )
            
            return ServerHealth(
                server_name=server_name,
                timestamp=datetime.now(),
                overall_status=overall_status,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                response_time=response_time,
                uptime=uptime_hours,
                active_connections=active_connections,
                load_average=list(load_avg)
            )
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            raise
    
    def calculate_overall_status(self, cpu: float, memory: float, 
                               disk: float, response_time: float) -> str:
        """Calculate overall server health status"""
        thresholds = self.health_thresholds
        
        # Check for critical conditions
        if (cpu >= thresholds['cpu_critical'] or 
            memory >= thresholds['memory_critical'] or
            disk >= thresholds['disk_critical'] or
            response_time >= thresholds['response_time_critical']):
            return 'critical'
        
        # Check for warning conditions
        if (cpu >= thresholds['cpu_warning'] or 
            memory >= thresholds['memory_warning'] or
            disk >= thresholds['disk_warning'] or
            response_time >= thresholds['response_time_warning']):
            return 'warning'
        
        return 'healthy'
    
    async def measure_response_time(self, server_name: str) -> float:
        """Measure server response time"""
        try:
            start_time = time.time()
            
            # For localhost, measure internal response time
            if server_name == 'localhost':
                # Simple internal latency test
                await asyncio.sleep(0.001)  # Simulate minimal processing
                response_time = (time.time() - start_time) * 1000
            else:
                # For remote servers, use HTTP ping
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://{server_name}', 
                                         timeout=aiohttp.ClientTimeout(total=5)) as response:
                        response_time = (time.time() - start_time) * 1000
            
            return response_time
            
        except Exception as e:
            logger.warning(f"Failed to measure response time for {server_name}: {e}")
            return 5000.0  # Return high response time on failure
    
    async def store_health_metrics(self, health: ServerHealth):
        """Store health metrics in database"""
        try:
            conn = await self.db_manager.get_connection()
            
            # Store individual metrics
            metrics = [
                ('cpu_usage', health.cpu_usage, '%', 
                 self.get_metric_status(health.cpu_usage, 'cpu')),
                ('memory_usage', health.memory_usage, '%', 
                 self.get_metric_status(health.memory_usage, 'memory')),
                ('disk_usage', health.disk_usage, '%', 
                 self.get_metric_status(health.disk_usage, 'disk')),
                ('response_time', health.response_time, 'ms', 
                 self.get_metric_status(health.response_time, 'response_time')),
                ('uptime', health.uptime, 'hours', 'healthy'),
                ('active_connections', health.active_connections, 'count', 'healthy')
            ]
            
            for metric_name, value, unit, status in metrics:
                await conn.execute("""
                    INSERT INTO server_health_metrics 
                    (server_name, metric_name, value, unit, status, threshold_warning, threshold_critical)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, health.server_name, metric_name, value, unit, status,
                self.health_thresholds.get(f'{metric_name}_warning'),
                self.health_thresholds.get(f'{metric_name}_critical'))
            
            # Update or insert health summary
            await conn.execute("""
                INSERT INTO server_health_summary 
                (server_name, overall_status, cpu_usage, memory_usage, disk_usage, 
                 response_time, uptime_hours, active_connections, load_average, network_io)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (server_name) DO UPDATE SET
                    last_check = CURRENT_TIMESTAMP,
                    overall_status = EXCLUDED.overall_status,
                    cpu_usage = EXCLUDED.cpu_usage,
                    memory_usage = EXCLUDED.memory_usage,
                    disk_usage = EXCLUDED.disk_usage,
                    response_time = EXCLUDED.response_time,
                    uptime_hours = EXCLUDED.uptime_hours,
                    active_connections = EXCLUDED.active_connections,
                    load_average = EXCLUDED.load_average,
                    network_io = EXCLUDED.network_io
            """, health.server_name, health.overall_status, health.cpu_usage,
            health.memory_usage, health.disk_usage, health.response_time,
            health.uptime, health.active_connections, 
            json.dumps(health.load_average), json.dumps(health.network_io))
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store health metrics: {e}")
            raise
    
    def get_metric_status(self, value: float, metric_type: str) -> str:
        """Get status for a specific metric value"""
        thresholds = self.health_thresholds
        
        warning_key = f'{metric_type}_warning'
        critical_key = f'{metric_type}_critical'
        
        if warning_key in thresholds and critical_key in thresholds:
            if value >= thresholds[critical_key]:
                return 'critical'
            elif value >= thresholds[warning_key]:
                return 'warning'
        
        return 'healthy'
    
    async def check_and_create_alerts(self, health: ServerHealth):
        """Check metrics and create alerts if needed"""
        try:
            conn = await self.db_manager.get_connection()
            
            alerts_to_create = []
            
            # Check CPU
            if health.cpu_usage >= self.health_thresholds['cpu_critical']:
                alerts_to_create.append({
                    'type': 'cpu_usage',
                    'severity': 'critical',
                    'message': f'CPU usage critical: {health.cpu_usage:.1f}%',
                    'value': health.cpu_usage,
                    'threshold': self.health_thresholds['cpu_critical']
                })
            elif health.cpu_usage >= self.health_thresholds['cpu_warning']:
                alerts_to_create.append({
                    'type': 'cpu_usage',
                    'severity': 'warning',
                    'message': f'CPU usage high: {health.cpu_usage:.1f}%',
                    'value': health.cpu_usage,
                    'threshold': self.health_thresholds['cpu_warning']
                })
            
            # Check Memory
            if health.memory_usage >= self.health_thresholds['memory_critical']:
                alerts_to_create.append({
                    'type': 'memory_usage',
                    'severity': 'critical',
                    'message': f'Memory usage critical: {health.memory_usage:.1f}%',
                    'value': health.memory_usage,
                    'threshold': self.health_thresholds['memory_critical']
                })
            elif health.memory_usage >= self.health_thresholds['memory_warning']:
                alerts_to_create.append({
                    'type': 'memory_usage',
                    'severity': 'warning',
                    'message': f'Memory usage high: {health.memory_usage:.1f}%',
                    'value': health.memory_usage,
                    'threshold': self.health_thresholds['memory_warning']
                })
            
            # Check Disk
            if health.disk_usage >= self.health_thresholds['disk_critical']:
                alerts_to_create.append({
                    'type': 'disk_usage',
                    'severity': 'critical',
                    'message': f'Disk usage critical: {health.disk_usage:.1f}%',
                    'value': health.disk_usage,
                    'threshold': self.health_thresholds['disk_critical']
                })
            elif health.disk_usage >= self.health_thresholds['disk_warning']:
                alerts_to_create.append({
                    'type': 'disk_usage',
                    'severity': 'warning',
                    'message': f'Disk usage high: {health.disk_usage:.1f}%',
                    'value': health.disk_usage,
                    'threshold': self.health_thresholds['disk_warning']
                })
            
            # Check Response Time
            if health.response_time >= self.health_thresholds['response_time_critical']:
                alerts_to_create.append({
                    'type': 'response_time',
                    'severity': 'critical',
                    'message': f'Response time critical: {health.response_time:.0f}ms',
                    'value': health.response_time,
                    'threshold': self.health_thresholds['response_time_critical']
                })
            elif health.response_time >= self.health_thresholds['response_time_warning']:
                alerts_to_create.append({
                    'type': 'response_time',
                    'severity': 'warning',
                    'message': f'Response time high: {health.response_time:.0f}ms',
                    'value': health.response_time,
                    'threshold': self.health_thresholds['response_time_warning']
                })
            
            # Create alerts in database
            for alert in alerts_to_create:
                await conn.execute("""
                    INSERT INTO health_alerts 
                    (server_name, alert_type, severity, message, metric_value, threshold_value)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, health.server_name, alert['type'], alert['severity'], 
                alert['message'], alert['value'], alert['threshold'])
            
            # Update alert count in summary
            if alerts_to_create:
                await conn.execute("""
                    UPDATE server_health_summary 
                    SET alerts_count = alerts_count + $1, last_alert = CURRENT_TIMESTAMP
                    WHERE server_name = $2
                """, len(alerts_to_create), health.server_name)
            
            await conn.close()
            return alerts_to_create
            
        except Exception as e:
            logger.error(f"Failed to check and create alerts: {e}")
            return []
    
    async def get_health_summary(self, server_name: str = None) -> Dict[str, Any]:
        """Get health summary for servers"""
        try:
            conn = await self.db_manager.get_connection()
            
            if server_name:
                query = "SELECT * FROM server_health_summary WHERE server_name = $1"
                rows = await conn.fetch(query, server_name)
            else:
                query = "SELECT * FROM server_health_summary ORDER BY last_check DESC"
                rows = await conn.fetch(query)
            
            await conn.close()
            
            return {
                'servers': [dict(row) for row in rows],
                'total_servers': len(rows),
                'healthy_servers': len([r for r in rows if r['overall_status'] == 'healthy']),
                'warning_servers': len([r for r in rows if r['overall_status'] == 'warning']),
                'critical_servers': len([r for r in rows if r['overall_status'] == 'critical']),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get health summary: {e}")
            return {'error': str(e)}
    
    async def get_recent_alerts(self, hours: int = 24, severity: str = None) -> List[Dict[str, Any]]:
        """Get recent health alerts"""
        try:
            conn = await self.db_manager.get_connection()
            
            base_query = """
                SELECT * FROM health_alerts 
                WHERE created_at >= $1
            """
            params = [datetime.now() - timedelta(hours=hours)]
            
            if severity:
                base_query += " AND severity = $2"
                params.append(severity)
            
            base_query += " ORDER BY created_at DESC LIMIT 100"
            
            rows = await conn.fetch(base_query, *params)
            await conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    async def start_monitoring(self, servers: List[str] = None):
        """Start continuous health monitoring"""
        if servers is None:
            servers = ['localhost']
        
        self.monitoring_active = True
        logger.info(f"Starting health monitoring for servers: {servers}")
        
        while self.monitoring_active:
            try:
                for server_name in servers:
                    # Get health metrics
                    health = await self.get_system_metrics(server_name)
                    
                    # Store metrics
                    await self.store_health_metrics(health)
                    
                    # Check for alerts
                    alerts = await self.check_and_create_alerts(health)
                    
                    if alerts:
                        logger.warning(f"Created {len(alerts)} alerts for {server_name}")
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        logger.info("Health monitoring stopped")

# Global instance
health_monitor = ServerHealthMonitor()
