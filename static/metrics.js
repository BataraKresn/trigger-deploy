// =================================
// Metrics Dashboard JavaScript
// =================================

class MetricsDashboard {
    constructor() {
        this.init();
        this.loadMetrics();
        
        // Auto-refresh every 30 seconds
        setInterval(() => this.loadMetrics(), 30000);
    }
    
    init() {
        console.log('Metrics Dashboard initialized');
    }
    
    async loadMetrics() {
        try {
            // Load all metrics in parallel
            const [stats, history, serverStats, systemInfo] = await Promise.all([
                fetch('/api/metrics/stats'),
                fetch('/api/metrics/history'),
                fetch('/api/metrics/servers'),
                fetch('/api/metrics/system')
            ]);
            
            if (stats.ok) {
                const statsData = await stats.json();
                this.updateStatsCards(statsData);
            }
            
            if (history.ok) {
                const historyData = await history.json();
                this.updateDeploymentHistory(historyData);
            }
            
            if (serverStats.ok) {
                const serverData = await serverStats.json();
                this.updateServerStats(serverData);
            }
            
            if (systemInfo.ok) {
                const systemData = await systemInfo.json();
                this.updateSystemInfo(systemData);
            }
            
        } catch (error) {
            console.error('Error loading metrics:', error);
            this.showError('Failed to load metrics data');
        }
    }
    
    updateStatsCards(stats) {
        document.getElementById('totalDeployments').textContent = stats.total || 0;
        document.getElementById('successfulDeployments').textContent = stats.success || 0;
        document.getElementById('failedDeployments').textContent = stats.failed || 0;
        document.getElementById('successRate').textContent = `${stats.success_rate || 0}%`;
        document.getElementById('inProgressDeployments').textContent = stats.in_progress || 0;
        document.getElementById('uptime').textContent = this.formatUptime(stats.uptime || 0);
    }
    
    updateDeploymentHistory(history) {
        const container = document.getElementById('deploymentHistory');
        
        if (!history.deployments || history.deployments.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    📝 No deployment history available yet.
                </div>
            `;
            return;
        }
        
        const tableHtml = `
            <table class="history-table">
                <thead>
                    <tr>
                        <th>Server</th>
                        <th>Status</th>
                        <th>Started</th>
                        <th>Duration</th>
                        <th>Client IP</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${history.deployments.map(deployment => `
                        <tr>
                            <td><strong>${deployment.server_name}</strong><br>
                                <small class="text-muted">${deployment.server_ip}</small>
                            </td>
                            <td>
                                <span class="status-badge ${this.getStatusClass(deployment)}">
                                    ${this.getStatusText(deployment)}
                                </span>
                            </td>
                            <td>${this.formatDateTime(deployment.started_at)}</td>
                            <td>${this.formatDuration(deployment.duration)}</td>
                            <td><code>${deployment.client_ip}</code></td>
                            <td>
                                ${deployment.log_file ? 
                                    `<a href="/logs/${deployment.log_file}" class="btn btn-small btn-secondary">📄 View Log</a>` : 
                                    '-'
                                }
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHtml;
    }
    
    updateServerStats(serverStats) {
        const container = document.getElementById('serverStats');
        
        if (!serverStats.servers || Object.keys(serverStats.servers).length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    📝 No server statistics available yet.
                </div>
            `;
            return;
        }
        
        const serversHtml = Object.entries(serverStats.servers).map(([serverName, stats]) => `
            <div class="server-stat-card" style="border: 1px solid #dee2e6; padding: 1rem; margin-bottom: 1rem; border-radius: 8px;">
                <h4>🖥️ ${serverName}</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; margin-top: 0.5rem;">
                    <div>
                        <strong>Total:</strong> ${stats.total}
                    </div>
                    <div>
                        <strong>Success:</strong> <span class="text-success">${stats.success}</span>
                    </div>
                    <div>
                        <strong>Failed:</strong> <span class="text-danger">${stats.failed}</span>
                    </div>
                    <div>
                        <strong>Last Deploy:</strong><br>
                        <small>${stats.last_deployment ? this.formatDateTime(stats.last_deployment) : 'Never'}</small>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = serversHtml;
    }
    
    updateSystemInfo(systemInfo) {
        const container = document.getElementById('systemInfo');
        
        const infoHtml = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                <div>
                    <h5>🐍 Python Version</h5>
                    <p>${systemInfo.python_version || 'Unknown'}</p>
                </div>
                <div>
                    <h5>🌐 Flask Version</h5>
                    <p>${systemInfo.flask_version || 'Unknown'}</p>
                </div>
                <div>
                    <h5>💾 Memory Usage</h5>
                    <p>${systemInfo.memory_usage || 'Unknown'}</p>
                </div>
                <div>
                    <h5>💽 Disk Usage</h5>
                    <p>${systemInfo.disk_usage || 'Unknown'}</p>
                </div>
                <div>
                    <h5>⚡ CPU Usage</h5>
                    <p>${systemInfo.cpu_usage || 'Unknown'}</p>
                </div>
                <div>
                    <h5>🕐 Server Time</h5>
                    <p>${new Date().toLocaleString()}</p>
                </div>
            </div>
        `;
        
        container.innerHTML = infoHtml;
    }
    
    getStatusClass(deployment) {
        if (deployment.success === true) return 'status-success';
        if (deployment.success === false) return 'status-failed';
        return 'status-running';
    }
    
    getStatusText(deployment) {
        if (deployment.success === true) return '✅ Success';
        if (deployment.success === false) return '❌ Failed';
        return '🔄 Running';
    }
    
    formatDateTime(isoString) {
        if (!isoString) return '-';
        return new Date(isoString).toLocaleString();
    }
    
    formatDuration(seconds) {
        if (!seconds) return '-';
        
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hrs > 0) return `${hrs}h ${mins}m ${secs}s`;
        if (mins > 0) return `${mins}m ${secs}s`;
        return `${secs}s`;
    }
    
    formatUptime(seconds) {
        if (!seconds) return '-';
        
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) return `${days}d ${hours}h`;
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    }
    
    showError(message) {
        // You can implement error display here
        console.error(message);
    }
}

// Global functions
function refreshMetrics() {
    if (window.metricsDashboard) {
        window.metricsDashboard.loadMetrics();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.metricsDashboard = new MetricsDashboard();
});
