# =================================
# Deployment History Manager
# =================================

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.models.config import config
from src.models.entities import Deployment


class DeploymentHistory:
    """Manage deployment history and statistics"""
    
    def __init__(self, history_file: str = None):
        self.history_file = history_file or os.path.join("logs", "deployment_history.json")
        self.ensure_history_file()
    
    def ensure_history_file(self):
        """Create history file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
    
    def add_deployment(self, deployment: Deployment):
        """Add a new deployment record"""
        try:
            history = self.get_all_deployments()
            history.append(deployment.to_dict())
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            print(f"Error adding deployment: {e}")
    
    def update_deployment(self, deployment_id: str, updates: Dict):
        """Update an existing deployment record"""
        try:
            history = self.get_all_deployments()
            
            for i, deployment in enumerate(history):
                if deployment.get('deployment_id') == deployment_id:
                    history[i].update(updates)
                    break
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            print(f"Error updating deployment: {e}")
    
    def get_all_deployments(self) -> List[Dict]:
        """Get all deployment records"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading history: {e}")
            return []
    
    def get_recent_deployments(self, limit: int = 10) -> List[Dict]:
        """Get recent deployments"""
        deployments = self.get_all_deployments()
        # Sort by started_at in descending order
        deployments.sort(key=lambda x: x.get('started_at', ''), reverse=True)
        return deployments[:limit]
    
    def get_deployment_stats(self) -> Dict:
        """Get deployment statistics"""
        deployments = self.get_all_deployments()
        
        total = len(deployments)
        success = len([d for d in deployments if d.get('status') == 'success'])
        failed = len([d for d in deployments if d.get('status') == 'failed'])
        in_progress = len([d for d in deployments if d.get('status') == 'running'])
        
        success_rate = (success / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'success': success,
            'failed': failed,
            'in_progress': in_progress,
            'success_rate': round(success_rate, 1)
        }
    
    def cleanup_old_deployments(self, days: int = 30):
        """Remove deployment records older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deployments = self.get_all_deployments()
            
            filtered_deployments = []
            for deployment in deployments:
                started_at = deployment.get('started_at')
                if started_at:
                    try:
                        deployment_date = datetime.fromisoformat(started_at)
                        if deployment_date > cutoff_date:
                            filtered_deployments.append(deployment)
                    except ValueError:
                        # Keep deployments with invalid dates
                        filtered_deployments.append(deployment)
                else:
                    # Keep deployments without started_at
                    filtered_deployments.append(deployment)
            
            with open(self.history_file, 'w') as f:
                json.dump(filtered_deployments, f, indent=2, default=str)
            
            removed_count = len(deployments) - len(filtered_deployments)
            print(f"Cleaned up {removed_count} old deployment records")
            
        except Exception as e:
            print(f"Error cleaning up deployments: {e}")


# Global deployment history instance
deployment_history = DeploymentHistory()
