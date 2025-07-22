// =================================
// Metrics Dashboard JavaScript
// =================================

// Global variables
let metricsInterval = null;
let deploymentHistory = [];
let systemStats = {};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Metrics page loaded');
    loadInitialMetrics();
    setupEventListeners();
    startAutoRefresh();
});

function setupEventListeners() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadInitialMetrics);
    }
    
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', toggleAutoRefresh);
    }
}

function loadInitialMetrics() {
    showSpinner();
    
    Promise.all([
        loadDeploymentHistory(),
        loadSystemStats(),
        loadServerMetrics()
    ])
    .then(() => {
        hideSpinner();
        updateLastRefresh();
    })
    .catch(error => {
        hideSpinner();
        showStatus(`❌ Error loading metrics: ${error.message}`, 'error');
        console.error('Metrics loading error:', error);
    });
}

function loadDeploymentHistory() {
    return fetch('/api/metrics/history')
    .then(response => response.json())
    .then(data => {
        deploymentHistory = data || [];
        displayDeploymentHistory(deploymentHistory);
        updateDeploymentStats(deploymentHistory);
    });
}

function loadSystemStats() {
    return fetch('/api/metrics/system')
    .then(response => response.json())
    .then(data => {
        systemStats = data;
        displaySystemStats(data);
    });
}

function loadServerMetrics() {
    return fetch('/api/metrics/servers')
    .then(response => response.json())
    .then(data => {
        displayServerMetrics(data);
    });
}

function displayDeploymentHistory(history) {
    const historyContainer = document.getElementById('deploymentHistory');
    if (!historyContainer) return;
    
    if (history.length === 0) {
        historyContainer.innerHTML = '<p class="text-muted">No deployment history available.</p>';
        return;
    }
    
    const historyItems = history.slice(0, 10).map(deployment => {
        const statusIcon = getDeploymentStatusIcon(deployment.status);
        const statusClass = getDeploymentStatusClass(deployment.status);
        const duration = deployment.duration ? `${deployment.duration.toFixed(1)}s` : 'N/A';
        const startTime = new Date(deployment.started_at).toLocaleString();
        
        return `
            <div class="deployment-item ${statusClass}">
                <div class="deployment-header">
                    <span class="deployment-status">${statusIcon} ${deployment.status}</span>
                    <span class="deployment-time">${startTime}</span>
                </div>
                <div class="deployment-details">
                    <p><strong>Server:</strong> ${deployment.server_name} (${deployment.server_ip})</p>
                    <p><strong>Duration:</strong> ${duration}</p>
                    <p><strong>Client:</strong> ${deployment.client_ip}</p>
                    ${deployment.log_file ? `<p><strong>Log:</strong> <a href="/logs/${deployment.log_file}" target="_blank">${deployment.log_file}</a></p>` : ''}
                </div>
                <div class="deployment-id">
                    <small>ID: ${deployment.deployment_id}</small>
                </div>
            </div>
        `;
    }).join('');
    
    historyContainer.innerHTML = historyItems;
}

function updateDeploymentStats(history) {
    const totalDeployments = history.length;
    const successfulDeployments = history.filter(d => d.status === 'success').length;
    const failedDeployments = history.filter(d => d.status === 'failed').length;
    const successRate = totalDeployments > 0 ? ((successfulDeployments / totalDeployments) * 100).toFixed(1) : 0;
    
    // Update stats cards
    updateStatCard('totalDeployments', totalDeployments);
    updateStatCard('successfulDeployments', successfulDeployments);
    updateStatCard('failedDeployments', failedDeployments);
    updateStatCard('successRate', `${successRate}%`);
}

function displaySystemStats(stats) {
    updateStatCard('cpuUsage', `${stats.cpu_percent}%`);
    updateStatCard('memoryUsage', `${stats.memory_percent}%`);
    updateStatCard('diskUsage', `${stats.disk_percent}%`);
    updateStatCard('uptime', formatUptime(stats.uptime));
    
    // Update system info
    const systemInfo = document.getElementById('systemInfo');
    if (systemInfo) {
        systemInfo.innerHTML = `
            <div class="system-info-grid">
                <div class="info-item">
                    <strong>Platform:</strong> ${stats.platform}
                </div>
                <div class="info-item">
                    <strong>Architecture:</strong> ${stats.architecture}
                </div>
                <div class="info-item">
                    <strong>Hostname:</strong> ${stats.hostname}
                </div>
                <div class="info-item">
                    <strong>CPU Cores:</strong> ${stats.cpu_count}
                </div>
                <div class="info-item">
                    <strong>Memory:</strong> ${formatBytes(stats.memory_total)}
                </div>
                <div class="info-item">
                    <strong>Disk:</strong> ${formatBytes(stats.disk_total)}
                </div>
            </div>
        `;
    }
}

function displayServerMetrics(servers) {
    const serverMetrics = document.getElementById('serverMetrics');
    if (!serverMetrics) return;
    
    if (!servers || servers.length === 0) {
        serverMetrics.innerHTML = '<p class="text-muted">No server metrics available.</p>';
        return;
    }
    
    const serverCards = servers.map(server => {
        const statusClass = getStatusClass(server.status);
        const statusIcon = getStatusIcon(server.status);
        
        return `
            <div class="server-metric-card ${statusClass}">
                <div class="server-metric-header">
                    <h4>${server.name}</h4>
                    <span class="server-status">${statusIcon} ${server.status}</span>
                </div>
                <div class="server-metric-details">
                    <p><strong>IP:</strong> ${server.ip}</p>
                    <p><strong>Type:</strong> ${server.type}</p>
                    <p><strong>Last Check:</strong> ${new Date().toLocaleString()}</p>
                </div>
            </div>
        `;
    }).join('');
    
    serverMetrics.innerHTML = serverCards;
}

function updateStatCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function getDeploymentStatusIcon(status) {
    switch(status) {
        case 'success': return '✅';
        case 'failed': return '❌';
        case 'running': return '🔄';
        case 'started': return '🚀';
        default: return '❓';
    }
}

function getDeploymentStatusClass(status) {
    switch(status) {
        case 'success': return 'deployment-success';
        case 'failed': return 'deployment-failed';
        case 'running': return 'deployment-running';
        case 'started': return 'deployment-started';
        default: return 'deployment-unknown';
    }
}

function getStatusClass(status) {
    switch(status) {
        case 'online': return 'status-online';
        case 'offline': return 'status-offline';
        default: return 'status-unknown';
    }
}

function getStatusIcon(status) {
    switch(status) {
        case 'online': return '🟢';
        case 'offline': return '🔴';
        default: return '🟡';
    }
}

function formatUptime(uptimeString) {
    try {
        const uptime = new Date(uptimeString);
        const now = new Date();
        const diffMs = now - uptime;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        
        if (diffDays > 0) {
            return `${diffDays}d ${diffHours}h`;
        } else if (diffHours > 0) {
            return `${diffHours}h`;
        } else {
            const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
            return `${diffMinutes}m`;
        }
    } catch (e) {
        return 'N/A';
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function startAutoRefresh() {
    const interval = 30000; // 30 seconds
    
    metricsInterval = setInterval(() => {
        const autoRefreshToggle = document.getElementById('autoRefreshToggle');
        if (autoRefreshToggle && autoRefreshToggle.checked) {
            loadInitialMetrics();
        }
    }, interval);
}

function toggleAutoRefresh(e) {
    const isEnabled = e.target.checked;
    const status = isEnabled ? 'enabled' : 'disabled';
    showStatus(`🔄 Auto-refresh ${status}`, 'info');
}

function updateLastRefresh() {
    const lastRefreshElement = document.getElementById('lastRefresh');
    if (lastRefreshElement) {
        lastRefreshElement.textContent = `Last updated: ${new Date().toLocaleString()}`;
    }
}

// Utility Functions
function showStatus(message, type = 'info') {
    const status = document.getElementById('status');
    if (!status) return;
    
    status.className = `alert alert-${type}`;
    status.textContent = message;
    status.classList.remove('hidden');
    
    setTimeout(() => hideStatus(), 3000);
}

function hideStatus() {
    const status = document.getElementById('status');
    if (status) {
        status.classList.add('hidden');
    }
}

function showSpinner() {
    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.classList.remove('hidden');
    }
}

function hideSpinner() {
    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.classList.add('hidden');
    }
}

// Cleanup interval on page unload
window.addEventListener('beforeunload', function() {
    if (metricsInterval) {
        clearInterval(metricsInterval);
    }
});
