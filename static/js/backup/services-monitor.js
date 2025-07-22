// =================================
// Services Monitor JavaScript
// =================================

// Global variables
let monitoringInterval = null;
let servicesData = {};
let isMonitoring = true;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Services Monitor page loaded');
    loadServicesStatus();
    setupEventListeners();
    startMonitoring();
});

function setupEventListeners() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadServicesStatus);
    }
    
    const toggleBtn = document.getElementById('toggleBtn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleMonitoring);
    }
}

function loadServicesStatus() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.textContent = '🔄 Refreshing...';
        refreshBtn.disabled = true;
    }
    
    showSpinner();
    
    fetch('/api/services/status')
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        servicesData = data;
        
        displayLocalServices(data.local_services || []);
        displayRemoteServices(data.remote_services || []);
        updateSummaryCards(data.summary || {});
        updateLastUpdate(data.last_updated);
        
        if (refreshBtn) {
            refreshBtn.textContent = '🔄 Refresh Status';
            refreshBtn.disabled = false;
        }
    })
    .catch(error => {
        hideSpinner();
        showStatus(`❌ Error loading services: ${error.message}`, 'error');
        console.error('Services loading error:', error);
        
        if (refreshBtn) {
            refreshBtn.textContent = '🔄 Refresh Status';
            refreshBtn.disabled = false;
        }
    });
}

function displayLocalServices(services) {
    const container = document.getElementById('localServices');
    if (!container) return;
    
    if (services.length === 0) {
        container.innerHTML = '<p class="text-muted">No local Docker services found.</p>';
        return;
    }
    
    const serviceCards = services.map(service => {
        const statusClass = getServiceStatusClass(service.status);
        const statusIcon = getServiceStatusIcon(service.status);
        
        return `
            <div class="service-card ${statusClass} ${service.critical ? 'critical' : ''}">
                <div class="service-header">
                    <h4>${service.name || 'Unknown Service'}</h4>
                    <span class="service-status status-${service.status}">${statusIcon} ${service.status}</span>
                </div>
                <div class="service-details">
                    <p><strong>Container:</strong> ${service.container_name || 'N/A'}</p>
                    <p><strong>Image:</strong> ${service.image || 'N/A'}</p>
                    <p><strong>Ports:</strong> ${service.ports || 'N/A'}</p>
                    <p><strong>Created:</strong> ${service.created ? new Date(service.created).toLocaleString() : 'N/A'}</p>
                    ${service.uptime ? `<p><strong>Uptime:</strong> ${service.uptime}</p>` : ''}
                </div>
                <div class="service-actions">
                    <button onclick="checkSingleService('${service.container_name}')" class="btn btn-sm btn-info">
                        🔍 Check
                    </button>
                    ${service.health_endpoint ? `
                        <button onclick="openHealthEndpoint('${service.health_endpoint}')" class="btn btn-sm btn-secondary">
                            🌐 Health URL
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = serviceCards;
}

function displayRemoteServices(services) {
    const container = document.getElementById('remoteServices');
    if (!container) return;
    
    if (services.length === 0) {
        container.innerHTML = '<p class="text-muted">No remote services configured.</p>';
        return;
    }
    
    const serviceCards = services.map(service => {
        const statusClass = getServiceStatusClass(service.status);
        const statusIcon = getServiceStatusIcon(service.status);
        
        return `
            <div class="service-card ${statusClass} ${service.critical ? 'critical' : ''}">
                <div class="service-header">
                    <h4>${service.name || 'Unknown Service'}</h4>
                    <span class="service-status status-${service.status}">${statusIcon} ${service.status}</span>
                </div>
                <div class="service-details">
                    <p><strong>URL:</strong> <a href="${service.url}" target="_blank">${service.url}</a></p>
                    <p><strong>Type:</strong> HTTP Service</p>
                    <p><strong>Description:</strong> ${service.description || 'N/A'}</p>
                    ${service.response_time ? `<p><strong>Response Time:</strong> ${(service.response_time * 1000).toFixed(0)}ms</p>` : ''}
                    ${service.status_code ? `<p><strong>Status Code:</strong> ${service.status_code}</p>` : ''}
                </div>
                <div class="service-actions">
                    <button onclick="checkSingleService('${service.name}')" class="btn btn-sm btn-info">
                        🔍 Check
                    </button>
                    <button onclick="openServiceUrl('${service.url}')" class="btn btn-sm btn-secondary">
                        🌐 Open URL
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = serviceCards;
}

function updateSummaryCards(summary) {
    updateSummaryCard('totalServices', summary.total_services || 0);
    updateSummaryCard('healthyServices', summary.healthy_services || 0);
    updateSummaryCard('unhealthyServices', summary.unhealthy_services || 0);
    updateSummaryCard('criticalDown', summary.critical_down || 0);
}

function updateSummaryCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function updateLastUpdate(timestamp) {
    const element = document.getElementById('lastUpdate');
    if (element && timestamp) {
        element.textContent = `Last updated: ${new Date(timestamp).toLocaleString()}`;
    }
}

function getServiceStatusClass(status) {
    switch(status) {
        case 'healthy': return 'healthy';
        case 'unhealthy': return 'unhealthy';
        case 'running': return 'healthy';
        case 'exited': return 'unhealthy';
        case 'stopped': return 'unhealthy';
        default: return '';
    }
}

function getServiceStatusIcon(status) {
    switch(status) {
        case 'healthy': 
        case 'running': return '✅';
        case 'unhealthy': 
        case 'exited': 
        case 'stopped': return '❌';
        default: return '❓';
    }
}

function checkSingleService(serviceName) {
    showStatus(`🔍 Checking ${serviceName}...`, 'info');
    
    fetch(`/api/services/check/${serviceName}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showStatus(`❌ ${data.error}`, 'error');
        } else {
            const status = data.status === 'healthy' ? '✅' : '❌';
            showStatus(`${status} ${serviceName}: ${data.status}`, data.status === 'healthy' ? 'success' : 'warning');
            
            // Refresh services after check
            setTimeout(() => loadServicesStatus(), 1000);
        }
    })
    .catch(error => {
        showStatus(`❌ Check failed: ${error.message}`, 'error');
        console.error('Service check error:', error);
    });
}

function openHealthEndpoint(url) {
    window.open(url, '_blank');
}

function openServiceUrl(url) {
    window.open(url, '_blank');
}

function toggleMonitoring() {
    isMonitoring = !isMonitoring;
    const toggleBtn = document.getElementById('toggleBtn');
    
    if (isMonitoring) {
        startMonitoring();
        if (toggleBtn) {
            toggleBtn.textContent = '⏸️ Pause Monitoring';
        }
        showStatus('✅ Monitoring resumed', 'success');
    } else {
        stopMonitoring();
        if (toggleBtn) {
            toggleBtn.textContent = '▶️ Resume Monitoring';
        }
        showStatus('⏸️ Monitoring paused', 'warning');
    }
}

function startMonitoring() {
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
    }
    
    // Refresh every 30 seconds
    monitoringInterval = setInterval(() => {
        if (isMonitoring) {
            loadServicesStatus();
        }
    }, 30000);
}

function stopMonitoring() {
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
        monitoringInterval = null;
    }
}

function showConfig() {
    const modal = document.getElementById('configModal');
    const configJson = document.getElementById('configJson');
    
    if (modal) {
        modal.style.display = 'block';
        
        // Load current configuration
        fetch('/api/services/config')
        .then(response => response.json())
        .then(data => {
            if (configJson) {
                configJson.value = JSON.stringify(data, null, 2);
            }
        })
        .catch(error => {
            console.error('Config loading error:', error);
            if (configJson) {
                configJson.value = '// Error loading configuration';
            }
        });
    }
}

function closeConfigModal() {
    const modal = document.getElementById('configModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function saveConfig() {
    const configJson = document.getElementById('configJson');
    if (!configJson) return;
    
    try {
        const config = JSON.parse(configJson.value);
        
        fetch('/api/services/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            showStatus('✅ Configuration saved successfully', 'success');
            closeConfigModal();
            
            // Refresh services
            setTimeout(() => loadServicesStatus(), 1000);
        })
        .catch(error => {
            showStatus(`❌ Save failed: ${error.message}`, 'error');
            console.error('Config save error:', error);
        });
        
    } catch (e) {
        showStatus('❌ Invalid JSON configuration', 'error');
    }
}

function refreshServices() {
    loadServicesStatus();
}

// Utility Functions
function showStatus(message, type = 'info') {
    // Create status element if doesn't exist
    let status = document.getElementById('status');
    if (!status) {
        status = document.createElement('div');
        status.id = 'status';
        status.className = 'alert hidden';
        const content = document.querySelector('.content');
        if (content && content.firstChild) {
            content.insertBefore(status, content.firstChild);
        }
    }
    
    status.className = `alert alert-${type}`;
    status.textContent = message;
    status.classList.remove('hidden');
    
    // Auto hide after 5 seconds for non-error messages
    if (type !== 'error') {
        setTimeout(() => hideStatus(), 5000);
    }
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

// Modal close on outside click
window.onclick = function(event) {
    const modal = document.getElementById('configModal');
    if (event.target === modal) {
        closeConfigModal();
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopMonitoring();
});
