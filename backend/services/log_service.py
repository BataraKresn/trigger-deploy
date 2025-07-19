"""
Log management service for handling deployment and application logs
"""
import os
import glob
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from loguru import logger

from models import db
from models.deploy_log import DeployLog
from models.server import Server


class LogService:
    """Service for managing and retrieving logs"""
    
    def __init__(self):
        self.log_directory = os.path.join(os.getcwd(), 'logs')
        self.retention_days = int(os.getenv('DEPLOY_LOG_RETENTION_DAYS', 30))
        
        # Ensure log directory exists
        os.makedirs(self.log_directory, exist_ok=True)
    
    def get_deployment_logs(self, server_id: Optional[int] = None, 
                          limit: int = 50, status: Optional[str] = None,
                          start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> Dict:
        """
        Get deployment logs with filtering options
        
        Args:
            server_id: Filter by server ID
            limit: Maximum number of logs to return
            status: Filter by deployment status
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            
        Returns:
            Dict containing filtered deployment logs
        """
        try:
            query = DeployLog.query
            
            # Apply filters
            if server_id:
                query = query.filter_by(server_id=server_id)
            
            if status:
                query = query.filter_by(status=status)
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(DeployLog.created_at >= start_dt)
            
            if end_date:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(DeployLog.created_at <= end_dt)
            
            # Order by most recent first
            logs = query.order_by(db.desc(DeployLog.created_at)).limit(limit).all()
            
            return {
                'success': True,
                'message': f'Retrieved {len(logs)} deployment logs',
                'data': {
                    'logs': [log.to_dict() for log in logs],
                    'total_count': len(logs),
                    'filters_applied': {
                        'server_id': server_id,
                        'status': status,
                        'start_date': start_date,
                        'end_date': end_date,
                        'limit': limit
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get deployment logs: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to retrieve logs: {str(e)}",
                'data': None
            }
    
    def get_deployment_log_detail(self, log_id: int) -> Dict:
        """
        Get detailed information for a specific deployment log
        
        Args:
            log_id: ID of the deployment log
            
        Returns:
            Dict containing detailed log information
        """
        try:
            deploy_log = DeployLog.query.get(log_id)
            if not deploy_log:
                raise ValueError(f"Deployment log with ID {log_id} not found")
            
            return {
                'success': True,
                'message': 'Deployment log retrieved successfully',
                'data': deploy_log.to_dict(include_output=True)
            }
            
        except Exception as e:
            logger.error(f"Failed to get deployment log {log_id}: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to retrieve log: {str(e)}",
                'data': None
            }
    
    def get_file_logs(self, server_ip: Optional[str] = None, 
                     date_filter: Optional[str] = None) -> Dict:
        """
        Get log files from the filesystem
        
        Args:
            server_ip: Filter by server IP
            date_filter: Filter by date (YYYY-MM-DD format)
            
        Returns:
            Dict containing file-based logs
        """
        try:
            # Build file pattern
            if server_ip and date_filter:
                pattern = f"{server_ip}-{date_filter}*.log"
            elif server_ip:
                pattern = f"{server_ip}-*.log"
            elif date_filter:
                pattern = f"*-{date_filter}*.log"
            else:
                pattern = "*.log"
            
            # Find matching log files
            log_files = glob.glob(os.path.join(self.log_directory, pattern))
            log_files.sort(key=os.path.getmtime, reverse=True)  # Sort by modification time
            
            files_info = []
            for log_file in log_files:
                file_stat = os.stat(log_file)
                files_info.append({
                    'filename': os.path.basename(log_file),
                    'filepath': log_file,
                    'size': file_stat.st_size,
                    'size_formatted': self._format_file_size(file_stat.st_size),
                    'modified_at': datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc).isoformat(),
                    'created_at': datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc).isoformat()
                })
            
            return {
                'success': True,
                'message': f'Found {len(files_info)} log files',
                'data': {
                    'files': files_info,
                    'total_count': len(files_info),
                    'log_directory': self.log_directory,
                    'filters_applied': {
                        'server_ip': server_ip,
                        'date_filter': date_filter
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get file logs: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to retrieve file logs: {str(e)}",
                'data': None
            }
    
    def get_file_log_content(self, filename: str, lines: int = 100, 
                           tail: bool = True) -> Dict:
        """
        Get content of a specific log file
        
        Args:
            filename: Name of the log file
            lines: Number of lines to return
            tail: If True, return last N lines; if False, return first N lines
            
        Returns:
            Dict containing file content
        """
        try:
            # Validate filename (security check)
            if not filename.endswith('.log') or '/' in filename or '\\' in filename:
                raise ValueError("Invalid filename")
            
            filepath = os.path.join(self.log_directory, filename)
            
            if not os.path.exists(filepath):
                raise ValueError(f"Log file {filename} not found")
            
            # Read file content
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                if tail:
                    # Read last N lines
                    content_lines = self._tail_file(f, lines)
                else:
                    # Read first N lines
                    content_lines = []
                    for i, line in enumerate(f):
                        if i >= lines:
                            break
                        content_lines.append(line.rstrip('\n'))
            
            file_stat = os.stat(filepath)
            
            return {
                'success': True,
                'message': f'Retrieved content from {filename}',
                'data': {
                    'filename': filename,
                    'lines': content_lines,
                    'total_lines': len(content_lines),
                    'file_size': file_stat.st_size,
                    'file_size_formatted': self._format_file_size(file_stat.st_size),
                    'modified_at': datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc).isoformat(),
                    'tail_mode': tail,
                    'lines_requested': lines
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get file content for {filename}: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to read file: {str(e)}",
                'data': None
            }
    
    def search_logs(self, search_term: str, server_id: Optional[int] = None,
                   case_sensitive: bool = False, limit: int = 100) -> Dict:
        """
        Search through deployment logs
        
        Args:
            search_term: Term to search for
            server_id: Limit search to specific server
            case_sensitive: Whether search should be case sensitive
            limit: Maximum number of results to return
            
        Returns:
            Dict containing search results
        """
        try:
            query = DeployLog.query
            
            if server_id:
                query = query.filter_by(server_id=server_id)
            
            # Search in output and error_message fields
            if case_sensitive:
                search_filter = db.or_(
                    DeployLog.output.contains(search_term),
                    DeployLog.error_message.contains(search_term),
                    DeployLog.command.contains(search_term)
                )
            else:
                search_filter = db.or_(
                    DeployLog.output.ilike(f'%{search_term}%'),
                    DeployLog.error_message.ilike(f'%{search_term}%'),
                    DeployLog.command.ilike(f'%{search_term}%')
                )
            
            logs = query.filter(search_filter).order_by(
                db.desc(DeployLog.created_at)
            ).limit(limit).all()
            
            # Highlight search terms in results
            results = []
            for log in logs:
                log_dict = log.to_dict()
                # Add search highlights (simplified)
                log_dict['search_highlights'] = self._highlight_search_term(
                    log_dict, search_term, case_sensitive
                )
                results.append(log_dict)
            
            return {
                'success': True,
                'message': f'Found {len(results)} logs matching "{search_term}"',
                'data': {
                    'logs': results,
                    'total_count': len(results),
                    'search_term': search_term,
                    'case_sensitive': case_sensitive,
                    'server_id': server_id
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to search logs: {str(e)}")
            return {
                'success': False,
                'message': f"Search failed: {str(e)}",
                'data': None
            }
    
    def cleanup_old_logs(self, dry_run: bool = False) -> Dict:
        """
        Clean up old log files and database records
        
        Args:
            dry_run: If True, only return what would be deleted
            
        Returns:
            Dict containing cleanup results
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            
            # Find old database logs
            old_db_logs = DeployLog.query.filter(
                DeployLog.created_at < cutoff_date
            ).all()
            
            # Find old log files
            old_files = []
            for log_file in glob.glob(os.path.join(self.log_directory, "*.log")):
                file_stat = os.stat(log_file)
                file_date = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
                if file_date < cutoff_date:
                    old_files.append({
                        'filename': os.path.basename(log_file),
                        'filepath': log_file,
                        'size': file_stat.st_size,
                        'modified_at': file_date.isoformat()
                    })
            
            if dry_run:
                return {
                    'success': True,
                    'message': f'Dry run: Would delete {len(old_db_logs)} database logs and {len(old_files)} files',
                    'data': {
                        'cutoff_date': cutoff_date.isoformat(),
                        'retention_days': self.retention_days,
                        'old_database_logs': len(old_db_logs),
                        'old_files': old_files,
                        'dry_run': True
                    }
                }
            
            # Delete old database logs
            deleted_db_count = 0
            for log in old_db_logs:
                db.session.delete(log)
                deleted_db_count += 1
            
            db.session.commit()
            
            # Delete old files
            deleted_files = []
            for file_info in old_files:
                try:
                    os.remove(file_info['filepath'])
                    deleted_files.append(file_info['filename'])
                except Exception as e:
                    logger.warning(f"Failed to delete file {file_info['filename']}: {str(e)}")
            
            return {
                'success': True,
                'message': f'Cleanup completed: deleted {deleted_db_count} database logs and {len(deleted_files)} files',
                'data': {
                    'cutoff_date': cutoff_date.isoformat(),
                    'retention_days': self.retention_days,
                    'deleted_database_logs': deleted_db_count,
                    'deleted_files': deleted_files,
                    'dry_run': False
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup logs: {str(e)}")
            return {
                'success': False,
                'message': f"Cleanup failed: {str(e)}",
                'data': None
            }
    
    def _tail_file(self, file_obj, lines: int) -> List[str]:
        """Read last N lines from a file efficiently"""
        # Simple implementation - for large files, consider using more efficient algorithms
        content = file_obj.read().split('\n')
        return content[-lines:] if len(content) >= lines else content
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def _highlight_search_term(self, log_dict: Dict, search_term: str, 
                             case_sensitive: bool) -> Dict:
        """Add search term highlights to log data"""
        highlights = {}
        
        # Fields to search in
        search_fields = ['output', 'error_message', 'command']
        
        for field in search_fields:
            content = log_dict.get(field)
            if content:
                if case_sensitive:
                    if search_term in content:
                        highlights[field] = True
                else:
                    if search_term.lower() in content.lower():
                        highlights[field] = True
        
        return highlights
