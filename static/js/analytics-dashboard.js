/**
 * Analytics Dashboard JavaScript
 * Handles data visualization, real-time updates, and user interactions
 */

// Global variables
let charts = {};
let refreshInterval;
let currentConfigType = null;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupAutoRefresh();
});

/**
 * Initialize the analytics dashboard
 */
function initializeDashboard() {
    showLoading();
    
    // Load all dashboard data
    Promise.all([
        loadSummaryData(),
        loadDeploymentTrends(),
        loadSuccessRateChart(),
        loadServerPerformance(),
        loadResponseTimeTrends(),
        loadHealthData(),
        loadUserActivity(),
        loadConfigurationData()
    ]).then(() => {
        hideLoading();
        showSuccessMessage('Dashboard loaded successfully');
    }).catch(error => {
        hideLoading();
        showErrorMessage('Failed to load dashboard data: ' + error.message);
    });
}

/**
 * Setup auto-refresh for real-time data
 */
function setupAutoRefresh() {
    // Refresh data every 30 seconds
    refreshInterval = setInterval(() => {
        refreshCriticalData();
    }, 30000);
}

/**
 * Refresh critical data without full page reload
 */
function refreshCriticalData() {
    loadSummaryData();
    loadHealthData();
    // Don't refresh charts as often to avoid disruption
}

/**
 * Refresh all dashboard data
 */
function refreshAllData() {
    showLoading();
    initializeDashboard();
}

// =================================
// Summary Data Loading
// =================================

async function loadSummaryData() {
    try {
        const [deploymentsResponse, healthResponse] = await Promise.all([
            fetch('/api/analytics/deployment-stats'),
            fetch('/api/health/summary')
        ]);
        
        const deploymentsData = await deploymentsResponse.json();
        const healthData = await healthResponse.json();
        
        if (deploymentsData.success) {
            updateSummaryCards(deploymentsData.data);
        }
        
        if (healthData.success) {
            updateServerCount(healthData.data);
        }
        
    } catch (error) {
        console.error('Failed to load summary data:', error);
    }
}

function updateSummaryCards(data) {
    // Total deployments
    document.getElementById('total-deployments').textContent = data.total_deployments || 0;
    document.getElementById('deployments-change').textContent = 
        data.deployments_change ? `+${data.deployments_change} this week` : '';
    
    // Success rate
    const successRate = data.success_rate || 0;
    document.getElementById('success-rate').textContent = `${successRate.toFixed(1)}%`;
    
    const successRateChange = document.getElementById('success-rate-change');
    if (successRate >= 90) {
        successRateChange.textContent = 'Excellent';
        successRateChange.className = 'card-change positive';
    } else if (successRate >= 70) {
        successRateChange.textContent = 'Good';
        successRateChange.className = 'card-change';
    } else {
        successRateChange.textContent = 'Needs Attention';
        successRateChange.className = 'card-change negative';
    }
    
    // Average duration
    const avgDuration = data.average_duration || 0;
    document.getElementById('avg-duration').textContent = formatDuration(avgDuration);
    document.getElementById('duration-change').textContent = 
        data.duration_change ? `${data.duration_change}s vs last week` : '';
}

function updateServerCount(healthData) {
    const totalServers = healthData.total_servers || 0;
    const healthyServers = healthData.healthy_servers || 0;
    
    document.getElementById('active-servers').textContent = `${healthyServers}/${totalServers}`;
    
    const serversChange = document.getElementById('servers-change');
    if (healthyServers === totalServers) {
        serversChange.textContent = 'All Healthy';
        serversChange.className = 'card-change positive';
    } else {
        serversChange.textContent = `${totalServers - healthyServers} Issues`;
        serversChange.className = 'card-change negative';
    }
}

// =================================
// Chart Loading Functions
// =================================

async function loadDeploymentTrends() {
    try {
        const period = document.getElementById('trend-period').value;
        const response = await fetch(`/api/analytics/deployment-trends?days=${period}`);
        const data = await response.json();
        
        if (data.success) {
            createDeploymentTrendsChart(data.data);
        }
    } catch (error) {
        console.error('Failed to load deployment trends:', error);
    }
}

function createDeploymentTrendsChart(data) {
    const ctx = document.getElementById('deployment-trends-chart').getContext('2d');
    
    if (charts.deploymentTrends) {
        charts.deploymentTrends.destroy();
    }
    
    charts.deploymentTrends = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates || [],
            datasets: [{
                label: 'Successful Deployments',
                data: data.successful_deployments || [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4
            }, {
                label: 'Failed Deployments',
                data: data.failed_deployments || [],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

async function loadSuccessRateChart() {
    try {
        const response = await fetch('/api/analytics/deployment-stats');
        const data = await response.json();
        
        if (data.success) {
            createSuccessRateChart(data.data);
        }
    } catch (error) {
        console.error('Failed to load success rate chart:', error);
    }
}

function createSuccessRateChart(data) {
    const ctx = document.getElementById('success-rate-chart').getContext('2d');
    
    if (charts.successRate) {
        charts.successRate.destroy();
    }
    
    const successful = data.successful_deployments || 0;
    const failed = data.failed_deployments || 0;
    
    charts.successRate = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Successful', 'Failed'],
            datasets: [{
                data: [successful, failed],
                backgroundColor: ['#10b981', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

async function loadServerPerformance() {
    try {
        const response = await fetch('/api/analytics/server-performance');
        const data = await response.json();
        
        if (data.success) {
            createServerPerformanceChart(data.data);
        }
    } catch (error) {
        console.error('Failed to load server performance:', error);
    }
}

function createServerPerformanceChart(data) {
    const ctx = document.getElementById('server-performance-chart').getContext('2d');
    
    if (charts.serverPerformance) {
        charts.serverPerformance.destroy();
    }
    
    charts.serverPerformance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.servers || [],
            datasets: [{
                label: 'Average Response Time (ms)',
                data: data.response_times || [],
                backgroundColor: '#667eea',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

async function loadResponseTimeTrends() {
    try {
        const response = await fetch('/api/analytics/response-time-trends?days=7');
        const data = await response.json();
        
        if (data.success) {
            createResponseTimeTrendsChart(data.data);
        }
    } catch (error) {
        console.error('Failed to load response time trends:', error);
    }
}

function createResponseTimeTrendsChart(data) {
    const ctx = document.getElementById('response-time-chart').getContext('2d');
    
    if (charts.responseTime) {
        charts.responseTime.destroy();
    }
    
    charts.responseTime = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timestamps || [],
            datasets: [{
                label: 'Response Time (ms)',
                data: data.response_times || [],
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// =================================
// Health Monitoring Functions
// =================================

async function loadHealthData() {
    try {
        const [summaryResponse, alertsResponse, metricsResponse] = await Promise.all([
            fetch('/api/health/summary'),
            fetch('/api/health/alerts?hours=24'),
            fetch('/api/health/server/localhost')
        ]);
        
        const summaryData = await summaryResponse.json();
        const alertsData = await alertsResponse.json();
        const metricsData = await metricsResponse.json();
        
        if (summaryData.success) {
            updateHealthSummary(summaryData.data);
        }
        
        if (alertsData.success) {
            updateRecentAlerts(alertsData.data.alerts);
        }
        
        if (metricsData.success) {
            updateSystemMetrics(metricsData.data.metrics);
        }
        
    } catch (error) {
        console.error('Failed to load health data:', error);
        document.getElementById('health-summary').innerHTML = 
            '<div class="error">Failed to load health data</div>';
    }
}

function updateHealthSummary(data) {
    const healthSummary = document.getElementById('health-summary');
    
    const html = `
        <div class="health-stats">
            <div class="stat-item">
                <span class="status-indicator healthy"></span>
                <span>Healthy Servers: ${data.healthy_servers || 0}</span>
            </div>
            <div class="stat-item">
                <span class="status-indicator warning"></span>
                <span>Warning Servers: ${data.warning_servers || 0}</span>
            </div>
            <div class="stat-item">
                <span class="status-indicator critical"></span>
                <span>Critical Servers: ${data.critical_servers || 0}</span>
            </div>
            <div class="stat-item">
                <span class="status-indicator unknown"></span>
                <span>Total Servers: ${data.total_servers || 0}</span>
            </div>
        </div>
        <div class="health-timestamp">
            Last updated: ${formatTimestamp(data.last_updated)}
        </div>
    `;
    
    healthSummary.innerHTML = html;
}

function updateRecentAlerts(alerts) {
    const alertsContainer = document.getElementById('recent-alerts');
    
    if (!alerts || alerts.length === 0) {
        alertsContainer.innerHTML = '<div class="info-text">No recent alerts</div>';
        return;
    }
    
    const html = alerts.slice(0, 5).map(alert => `
        <div class="alert-item ${alert.severity}">
            <div class="alert-icon">
                <i class="fas ${getAlertIcon(alert.severity)}"></i>
            </div>
            <div class="alert-content">
                <div class="alert-message">${alert.message}</div>
                <div class="alert-time">${formatTimestamp(alert.created_at)}</div>
            </div>
        </div>
    `).join('');
    
    alertsContainer.innerHTML = html;
}

function updateSystemMetrics(metrics) {
    // CPU Usage
    updateMetricBar('cpu-usage', 'cpu-value', metrics.cpu_usage, '%');
    
    // Memory Usage
    updateMetricBar('memory-usage', 'memory-value', metrics.memory_usage, '%');
    
    // Disk Usage
    updateMetricBar('disk-usage', 'disk-value', metrics.disk_usage, '%');
    
    // Response Time (normalize to 0-100 scale based on max 5000ms)
    const responseTimePercent = Math.min((metrics.response_time / 5000) * 100, 100);
    updateMetricBar('response-time', 'response-time-value', responseTimePercent, 'ms', metrics.response_time);
}

function updateMetricBar(barId, valueId, percentage, unit, actualValue = null) {
    const bar = document.getElementById(barId);
    const valueElement = document.getElementById(valueId);
    
    if (bar && valueElement) {
        bar.style.width = `${percentage}%`;
        
        // Set color based on percentage
        bar.className = 'metric-fill';
        if (percentage >= 90) {
            bar.classList.add('critical');
        } else if (percentage >= 70) {
            bar.classList.add('warning');
        }
        
        // Update value text
        const displayValue = actualValue !== null ? actualValue : percentage;
        valueElement.textContent = `${displayValue.toFixed(1)}${unit}`;
    }
}

function refreshHealthData() {
    loadHealthData();
}

// =================================
// User Activity Functions
// =================================

async function loadUserActivity() {
    try {
        const period = document.getElementById('activity-period').value;
        const response = await fetch(`/api/analytics/user-activity?days=${period}`);
        const data = await response.json();
        
        if (data.success) {
            updateTopUsers(data.data.top_users);
            updateRecentActivity(data.data.recent_activity);
            createUserActivityChart(data.data);
        }
    } catch (error) {
        console.error('Failed to load user activity:', error);
    }
}

function updateTopUsers(users) {
    const container = document.getElementById('top-users');
    
    if (!users || users.length === 0) {
        container.innerHTML = '<div class="info-text">No user activity data</div>';
        return;
    }
    
    const html = users.map(user => `
        <div class="user-item">
            <div class="user-info">
                <strong>${user.username}</strong>
                <div class="user-stats">${user.deployment_count} deployments</div>
            </div>
            <div class="user-score">${user.success_rate.toFixed(1)}%</div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

function updateRecentActivity(activities) {
    const container = document.getElementById('recent-activity');
    
    if (!activities || activities.length === 0) {
        container.innerHTML = '<div class="info-text">No recent activity</div>';
        return;
    }
    
    const html = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-info">
                <strong>${activity.username}</strong>
                <div class="activity-description">${activity.action}</div>
            </div>
            <div class="activity-time">${formatTimestamp(activity.timestamp)}</div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

function createUserActivityChart(data) {
    const ctx = document.getElementById('user-activity-chart').getContext('2d');
    
    if (charts.userActivity) {
        charts.userActivity.destroy();
    }
    
    charts.userActivity = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates || [],
            datasets: [{
                label: 'Active Users',
                data: data.active_users || [],
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function updateUserActivity() {
    loadUserActivity();
}

function updateDeploymentTrends() {
    loadDeploymentTrends();
}

function refreshServerPerformance() {
    loadServerPerformance();
}

// =================================
// Configuration Management Functions
// =================================

async function loadConfigurationData() {
    try {
        // Load recent configuration changes
        const response = await fetch('/api/config/schemas');
        const data = await response.json();
        
        if (data.success) {
            // Configuration types are already hardcoded in the HTML
            // Just load recent changes for now
            loadConfigChanges();
        }
    } catch (error) {
        console.error('Failed to load configuration data:', error);
    }
}

async function loadConfigChanges() {
    // This would load recent configuration changes
    // For now, show placeholder data
    const container = document.getElementById('config-changes');
    
    container.innerHTML = `
        <div class="change-item">
            <div class="change-info">
                <strong>Servers Configuration</strong>
                <div class="change-description">Updated production server settings</div>
            </div>
            <div class="change-time">2 hours ago</div>
        </div>
        <div class="change-item">
            <div class="change-info">
                <strong>Services Configuration</strong>
                <div class="change-description">Added new monitoring endpoints</div>
            </div>
            <div class="change-time">1 day ago</div>
        </div>
    `;
}

async function loadConfigVersions(configType) {
    currentConfigType = configType;
    
    try {
        const response = await fetch(`/api/config/${configType}/versions?limit=10`);
        const data = await response.json();
        
        if (data.success) {
            updateConfigVersionsTable(data.data.versions);
        }
    } catch (error) {
        console.error('Failed to load config versions:', error);
    }
}

function updateConfigVersionsTable(versions) {
    const container = document.getElementById('config-versions');
    
    if (!versions || versions.length === 0) {
        container.innerHTML = '<div class="info-text">No configuration versions found</div>';
        return;
    }
    
    const html = `
        <div class="versions-header">
            <h4>Configuration Versions for ${currentConfigType}</h4>
        </div>
        <div class="versions-list">
            ${versions.map(version => `
                <div class="version-item ${version.is_active ? 'active' : ''}">
                    <div class="version-info">
                        <strong>${version.version_id}</strong>
                        <div class="version-description">${version.description || 'No description'}</div>
                        <div class="version-meta">
                            By ${version.author} • ${formatTimestamp(version.timestamp)}
                        </div>
                    </div>
                    <div class="version-actions">
                        ${version.is_active ? 
                            '<span class="status-badge active">Active</span>' : 
                            `<button class="btn-small" onclick="rollbackConfig('${version.version_id}')">Restore</button>`
                        }
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    container.innerHTML = html;
}

// =================================
// Configuration Modal Functions
// =================================

function openConfigModal() {
    document.getElementById('config-modal').style.display = 'block';
}

function closeConfigModal() {
    document.getElementById('config-modal').style.display = 'none';
    clearConfigForm();
}

function clearConfigForm() {
    document.getElementById('config-description').value = '';
    document.getElementById('config-data').value = '';
    document.getElementById('config-validation').innerHTML = '';
}

async function validateConfiguration() {
    const configType = document.getElementById('config-type-select').value;
    const configDataText = document.getElementById('config-data').value;
    
    if (!configDataText.trim()) {
        showConfigValidation('error', 'Please enter configuration data');
        return;
    }
    
    try {
        const configData = JSON.parse(configDataText);
        
        const response = await fetch(`/api/config/${configType}/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config_data: configData })
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (result.data.is_valid) {
                showConfigValidation('success', 'Configuration is valid!');
            } else {
                const errors = result.data.errors.join('<br>');
                showConfigValidation('error', `Validation errors:<br>${errors}`);
            }
        } else {
            showConfigValidation('error', result.error);
        }
        
    } catch (error) {
        showConfigValidation('error', 'Invalid JSON format');
    }
}

async function saveConfiguration() {
    const configType = document.getElementById('config-type-select').value;
    const description = document.getElementById('config-description').value;
    const configDataText = document.getElementById('config-data').value;
    
    if (!configDataText.trim()) {
        showConfigValidation('error', 'Please enter configuration data');
        return;
    }
    
    try {
        const configData = JSON.parse(configDataText);
        
        const response = await fetch(`/api/config/${configType}/versions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                config_data: configData,
                description: description,
                author: 'dashboard_user'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showConfigValidation('success', 'Configuration saved successfully!');
            setTimeout(() => {
                closeConfigModal();
                loadConfigVersions(configType);
            }, 2000);
        } else {
            showConfigValidation('error', result.error);
        }
        
    } catch (error) {
        showConfigValidation('error', 'Invalid JSON format');
    }
}

function showConfigValidation(type, message) {
    const container = document.getElementById('config-validation');
    container.className = `validation-result ${type}`;
    container.innerHTML = message;
}

async function rollbackConfig(versionId) {
    if (!confirm(`Are you sure you want to rollback to version ${versionId}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/config/${currentConfigType}/rollback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                target_version_id: versionId,
                author: 'dashboard_user'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessMessage('Configuration rolled back successfully');
            loadConfigVersions(currentConfigType);
        } else {
            showErrorMessage(result.error);
        }
        
    } catch (error) {
        showErrorMessage('Failed to rollback configuration');
    }
}

// =================================
// Utility Functions
// =================================

function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
        return `${(seconds / 60).toFixed(1)}m`;
    } else {
        return `${(seconds / 3600).toFixed(1)}h`;
    }
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) {
            return 'Just now';
        } else if (diffMins < 60) {
            return `${diffMins} minutes ago`;
        } else if (diffHours < 24) {
            return `${diffHours} hours ago`;
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else {
            return date.toLocaleDateString();
        }
    } catch (error) {
        return 'Unknown';
    }
}

function getAlertIcon(severity) {
    switch (severity) {
        case 'critical':
            return 'fa-exclamation-triangle';
        case 'warning':
            return 'fa-exclamation-circle';
        case 'info':
            return 'fa-info-circle';
        default:
            return 'fa-info-circle';
    }
}

function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

function showSuccessMessage(message) {
    // Simple notification - could be enhanced with a proper notification system
    console.log('Success:', message);
}

function showErrorMessage(message) {
    // Simple notification - could be enhanced with a proper notification system
    console.error('Error:', message);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Destroy all charts
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
});

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('config-modal');
    if (event.target === modal) {
        closeConfigModal();
    }
});
