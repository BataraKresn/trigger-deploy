"""
Deployment Analytics Module
Provides analytics and insights for deployment operations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class DeploymentAnalytics:
    """Analytics service for deployment data"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    async def get_deployment_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive deployment statistics"""
        try:
            async with self.db.pool.acquire() as conn:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Total deployments
                total = await conn.fetchval(
                    "SELECT COUNT(*) FROM deployments WHERE created_at >= $1",
                    start_date
                )
                
                # Successful deployments
                successful = await conn.fetchval(
                    "SELECT COUNT(*) FROM deployments WHERE status = 'success' AND created_at >= $1",
                    start_date
                )
                
                # Failed deployments
                failed = await conn.fetchval(
                    "SELECT COUNT(*) FROM deployments WHERE status = 'failed' AND created_at >= $1",
                    start_date
                )
                
                # Average deployment time
                avg_duration = await conn.fetchval(
                    "SELECT AVG(duration) FROM deployments WHERE duration IS NOT NULL AND created_at >= $1",
                    start_date
                )
                
                # Success rate
                success_rate = (successful / total * 100) if total > 0 else 0
                
                # Daily trends
                daily_stats = await conn.fetch("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                        AVG(duration) as avg_duration
                    FROM deployments 
                    WHERE created_at >= $1
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    LIMIT 30
                """, start_date)
                
                return {
                    'total_deployments': total,
                    'successful_deployments': successful,
                    'failed_deployments': failed,
                    'success_rate': round(success_rate, 2),
                    'avg_duration': round(float(avg_duration or 0), 2),
                    'daily_trends': [
                        {
                            'date': row['date'].isoformat(),
                            'total': row['total'],
                            'successful': row['successful'],
                            'success_rate': round((row['successful'] / row['total']) * 100, 2) if row['total'] > 0 else 0,
                            'avg_duration': round(float(row['avg_duration'] or 0), 2)
                        }
                        for row in daily_stats
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting deployment stats: {e}")
            return {
                'total_deployments': 0,
                'successful_deployments': 0,
                'failed_deployments': 0,
                'success_rate': 0,
                'avg_duration': 0,
                'daily_trends': []
            }
    
    async def get_server_performance(self) -> List[Dict[str, Any]]:
        """Get performance statistics by server"""
        try:
            async with self.db.pool.acquire() as conn:
                server_stats = await conn.fetch("""
                    SELECT 
                        server_name,
                        COUNT(*) as total_deployments,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_deployments,
                        AVG(duration) as avg_duration,
                        MAX(created_at) as last_deployment
                    FROM deployments 
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY server_name
                    ORDER BY total_deployments DESC
                """)
                
                return [
                    {
                        'server_name': row['server_name'],
                        'total_deployments': row['total_deployments'],
                        'successful_deployments': row['successful_deployments'],
                        'success_rate': round((row['successful_deployments'] / row['total_deployments']) * 100, 2) if row['total_deployments'] > 0 else 0,
                        'avg_duration': round(float(row['avg_duration'] or 0), 2),
                        'last_deployment': row['last_deployment'].isoformat() if row['last_deployment'] else None
                    }
                    for row in server_stats
                ]
        except Exception as e:
            logger.error(f"Error getting server performance: {e}")
            return []
    
    async def get_user_activity(self) -> List[Dict[str, Any]]:
        """Get user deployment activity"""
        try:
            async with self.db.pool.acquire() as conn:
                user_stats = await conn.fetch("""
                    SELECT 
                        d.triggered_by,
                        u.nama_lengkap,
                        COUNT(*) as total_deployments,
                        COUNT(CASE WHEN d.status = 'success' THEN 1 END) as successful_deployments,
                        MAX(d.created_at) as last_activity
                    FROM deployments d
                    LEFT JOIN users u ON d.triggered_by = u.username
                    WHERE d.created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY d.triggered_by, u.nama_lengkap
                    ORDER BY total_deployments DESC
                """)
                
                return [
                    {
                        'username': row['triggered_by'],
                        'full_name': row['nama_lengkap'] or 'Unknown User',
                        'total_deployments': row['total_deployments'],
                        'successful_deployments': row['successful_deployments'],
                        'success_rate': round((row['successful_deployments'] / row['total_deployments']) * 100, 2) if row['total_deployments'] > 0 else 0,
                        'last_activity': row['last_activity'].isoformat() if row['last_activity'] else None
                    }
                    for row in user_stats
                ]
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return []
    
    async def get_failure_analysis(self) -> Dict[str, Any]:
        """Analyze deployment failures"""
        try:
            async with self.db.pool.acquire() as conn:
                # Common error patterns
                error_patterns = await conn.fetch("""
                    SELECT 
                        CASE 
                            WHEN error_output ILIKE '%permission denied%' THEN 'Permission Denied'
                            WHEN error_output ILIKE '%connection refused%' THEN 'Connection Refused'
                            WHEN error_output ILIKE '%timeout%' THEN 'Timeout'
                            WHEN error_output ILIKE '%disk%full%' THEN 'Disk Full'
                            WHEN error_output ILIKE '%out of memory%' THEN 'Out of Memory'
                            ELSE 'Other Error'
                        END as error_category,
                        COUNT(*) as error_count
                    FROM deployments 
                    WHERE status = 'failed' 
                    AND error_output IS NOT NULL 
                    AND created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY error_category
                    ORDER BY error_count DESC
                """)
                
                # Failure rate by time of day
                hourly_failures = await conn.fetch("""
                    SELECT 
                        EXTRACT(HOUR FROM created_at) as hour,
                        COUNT(*) as failure_count
                    FROM deployments 
                    WHERE status = 'failed' 
                    AND created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY EXTRACT(HOUR FROM created_at)
                    ORDER BY hour
                """)
                
                return {
                    'error_patterns': [
                        {
                            'category': row['error_category'],
                            'count': row['error_count']
                        }
                        for row in error_patterns
                    ],
                    'hourly_failure_distribution': [
                        {
                            'hour': int(row['hour']),
                            'failure_count': row['failure_count']
                        }
                        for row in hourly_failures
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting failure analysis: {e}")
            return {
                'error_patterns': [],
                'hourly_failure_distribution': []
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Synchronous method to get basic deployment statistics
        """
        try:
            # Check if we have a database connection
            if not self.db or not hasattr(self.db, 'get_connection'):
                logger.warning("No database connection available for analytics")
                return self._get_mock_stats()
            
            # Try to get a database connection
            conn = self.db.get_connection()
            if not conn:
                logger.warning("Could not get database connection")
                return self._get_mock_stats()
            
            try:
                cursor = conn.cursor()
                
                # Get basic deployment stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                        AVG(CASE WHEN duration IS NOT NULL THEN duration END) as avg_duration
                    FROM deployments 
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                """)
                
                result = cursor.fetchone()
                
                if result:
                    total, successful, failed, avg_duration = result
                    success_rate = (successful / total * 100) if total > 0 else 0
                    
                    return {
                        'total_deployments': total or 0,
                        'successful_deployments': successful or 0,
                        'failed_deployments': failed or 0,
                        'success_rate': round(success_rate, 2),
                        'avg_duration': round(float(avg_duration or 0), 2)
                    }
                else:
                    return self._get_mock_stats()
                    
            except Exception as db_error:
                logger.warning(f"Database query failed: {db_error}")
                return self._get_mock_stats()
            finally:
                if conn:
                    self.db.return_connection(conn)
                    
        except Exception as e:
            logger.warning(f"Could not get deployment stats: {e}")
            return self._get_mock_stats()
    
    def _get_mock_stats(self) -> Dict[str, Any]:
        """Return mock statistics when database is not available"""
        return {
            'total_deployments': 0,
            'successful_deployments': 0,
            'failed_deployments': 0,
            'success_rate': 0,
            'avg_duration': 0
        }
