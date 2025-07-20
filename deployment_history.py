# =================================
# Deployment History Manager
# =================================

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class DeploymentHistory:
    def __init__(self, history_file="logs/deployment_history.json"):
        self.history_file = history_file
        self.ensure_history_file()
    
    def ensure_history_file(self):
        """Create history file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
    
    def add_deployment(self, server_name: str, server_ip: str, client_ip: str, 
                      log_file: str, status: str = "started") -> str:
        """Add new deployment record"""
        deployment_id = f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        deployment = {
            "id": deployment_id,
            "server_name": server_name,
            "server_ip": server_ip,
            "client_ip": client_ip,
            "log_file": log_file,
            "status": status,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "duration": None,
            "success": None
        }
        
        history = self.load_history()
        history.insert(0, deployment)  # Insert at beginning
        
        # Keep only last 100 deployments
        if len(history) > 100:
            history = history[:100]
        
        self.save_history(history)
        return deployment_id
    
    def update_deployment(self, deployment_id: str, status: str, success: bool = True):
        """Update deployment status"""
        history = self.load_history()
        
        for deployment in history:
            if deployment["id"] == deployment_id:
                deployment["status"] = status
                deployment["completed_at"] = datetime.now().isoformat()
                deployment["success"] = success
                
                # Calculate duration
                if deployment["started_at"]:
                    start_time = datetime.fromisoformat(deployment["started_at"])
                    end_time = datetime.now()
                    deployment["duration"] = int((end_time - start_time).total_seconds())
                
                break
        
        self.save_history(history)
    
    def load_history(self) -> List[Dict]:
        """Load deployment history"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    
    def save_history(self, history: List[Dict]):
        """Save deployment history"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def get_recent_deployments(self, limit: int = 20) -> List[Dict]:
        """Get recent deployments"""
        history = self.load_history()
        return history[:limit]
    
    def get_deployment_stats(self) -> Dict:
        """Get deployment statistics"""
        history = self.load_history()
        total = len(history)
        
        if total == 0:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "in_progress": 0,
                "success_rate": 0
            }
        
        success = len([d for d in history if d.get("success") is True])
        failed = len([d for d in history if d.get("success") is False])
        in_progress = len([d for d in history if d.get("status") in ["started", "running"]])
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "in_progress": in_progress,
            "success_rate": round((success / total) * 100, 1) if total > 0 else 0
        }
    
    def get_server_stats(self) -> Dict:
        """Get per-server deployment statistics"""
        history = self.load_history()
        server_stats = {}
        
        for deployment in history:
            server = deployment.get("server_name", "Unknown")
            if server not in server_stats:
                server_stats[server] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "last_deployment": None
                }
            
            server_stats[server]["total"] += 1
            
            if deployment.get("success") is True:
                server_stats[server]["success"] += 1
            elif deployment.get("success") is False:
                server_stats[server]["failed"] += 1
            
            # Update last deployment time
            if not server_stats[server]["last_deployment"] or \
               deployment.get("started_at", "") > server_stats[server]["last_deployment"]:
                server_stats[server]["last_deployment"] = deployment.get("started_at")
        
        return server_stats

# Global instance
deployment_history = DeploymentHistory()
