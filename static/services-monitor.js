// =================================
// Services Monitor JavaScript
// =================================

class ServicesMonitor {
    constructor() {
        this.monitoringActive = true;
        this.autoRefreshInterval = null;
        this.init();
        this.loadServices();
        
        // Auto-refresh every 30 seconds
        this.startAutoRefresh();
    }
    
    init() {
        console.log('Services Monitor initialized');
        
        // Setup modal event listeners
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('configModal');
            if (e.target === modal) {
                this.closeConfigModal();
            }
        });
    }
    
    async loadServices() {
        try {
            this.showLoading('Checking services...');
            
            const response = await fetch('/api/services/status');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.updateServicesDisplay(data);
            
        } catch (error) {
            console.error('Error loading services:', error);
            this.showError(`Failed to load services: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    updateServicesDisplay(data) {
        // Update summary cards
        this.updateSummaryCards(data.summary);
        
        // Update local services
        this.updateServicesList('localServices', data.local_services || []);
        
        // Update remote services
        this.updateServicesList('remoteServices', data.remote_services || []);
        
        // Update last update time
        document.getElementById('lastUpdate').textContent = 
            `Last updated: ${new Date(data.timestamp).toLocaleTimeString()}`;
    }
    
    updateSummaryCards(summary) {
        document.getElementById('totalServices').textContent = summary.total || 0;
        document.getElementById('healthyServices').textContent = summary.healthy || 0;
        document.getElementById('unhealthyServices').textContent = summary.unhealthy || 0;
        document.getElementById('criticalDown').textContent = summary.critical_down || 0;
    }
    
    updateServicesList(containerId, services) {
        const container = document.getElementById(containerId);
        
        if (!services || services.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info" style="grid-column: 1 / -1;">
                    📝 No services configured for monitoring.
                </div>
            `;
            return;
        }
        
        const servicesHtml = services.map(service => `
            <div class="service-card ${service.healthy ? 'healthy' : 'unhealthy'} ${service.critical && !service.healthy ? 'critical' : ''}">
                <div class="service-header">
                    <h4>${this.getServiceIcon(service)} ${service.name}</h4>
                    <span class="service-status ${service.healthy ? 'status-healthy' : 'status-unhealthy'}">
                        ${service.healthy ? '✅ Healthy' : '❌ Unhealthy'}
                    </span>
                </div>
                
                <div class="service-details">
                    <p><strong>Type:</strong> ${service.type}</p>
                    ${service.container_name ? `<p><strong>Container:</strong> ${service.container_name}</p>` : ''}
                    ${service.container_id ? `<p><strong>Container ID:</strong> <code>${service.container_id}</code></p>` : ''}
                    <p><strong>Status:</strong> ${service.status}</p>
                    ${service.response_time ? `<p><strong>Response Time:</strong> ${service.response_time.toFixed(2)}s</p>` : ''}
                    <p><strong>Critical:</strong> ${service.critical ? 'Yes' : 'No'}</p>
                    <p><strong>Last Check:</strong> ${new Date(service.checked_at).toLocaleTimeString()}</p>
                    
                    <div class="mt-2">
                        <small class="text-muted">${service.message}</small>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = servicesHtml;
    }
    
    getServiceIcon(service) {
        if (service.type === 'docker') return '🐳';
        if (service.type === 'http') return '🌐';
        if (service.type === 'tcp') return '🔌';
        return '⚙️';
    }
    
    async toggleMonitoring() {
        try {
            const btn = document.getElementById('toggleBtn');
            const newState = !this.monitoringActive;
            
            btn.disabled = true;
            btn.textContent = '⏳ Processing...';
            
            // Get token with modal if needed
            const token = await this.getToken();
            
            if (!token) {
                this.showError('Authentication cancelled');
                return;
            }
            
            const response = await fetch('/api/services/toggle-monitoring', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ enable: newState })
            });
            
            if (!response.ok) {
                // If unauthorized, clear stored token and try again
                if (response.status === 401) {
                    sessionStorage.removeItem('deployToken');
                    throw new Error('Invalid token. Please try again.');
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            this.monitoringActive = result.monitoring_active;
            
            // Update button
            btn.textContent = this.monitoringActive ? '⏸️ Pause Monitoring' : '▶️ Start Monitoring';
            btn.className = this.monitoringActive ? 'btn btn-warning' : 'btn btn-success';
            
            // Update auto-refresh
            if (this.monitoringActive) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
            
            this.showSuccess(result.message);
            
        } catch (error) {
            console.error('Error toggling monitoring:', error);
            this.showError(`Failed to toggle monitoring: ${error.message}`);
        } finally {
            document.getElementById('toggleBtn').disabled = false;
        }
    }
    
    async showConfig() {
        try {
            const response = await fetch('/api/services/config');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const config = await response.json();
            document.getElementById('configJson').value = JSON.stringify(config, null, 2);
            
            // Show modal with proper class
            const modal = document.getElementById('configModal');
            modal.style.display = 'flex';
            modal.classList.add('show');
            
            // Focus on textarea after a brief delay
            setTimeout(() => {
                document.getElementById('configJson').focus();
            }, 100);
            
        } catch (error) {
            console.error('Error loading config:', error);
            this.showError(`Failed to load configuration: ${error.message}`);
        }
    }
    
    closeConfigModal() {
        const modal = document.getElementById('configModal');
        modal.classList.remove('show');
        
        // Hide modal after animation
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
    
    async saveConfig() {
        try {
            const configText = document.getElementById('configJson').value;
            let config;
            
            try {
                config = JSON.parse(configText);
            } catch (e) {
                throw new Error('Invalid JSON format');
            }
            
            // Get token with modal if needed
            const token = await this.getToken();
            
            if (!token) {
                this.showError('Authentication cancelled');
                return;
            }
            
            const response = await fetch('/api/services/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(config)
            });
            
            if (!response.ok) {
                // If unauthorized, clear stored token
                if (response.status === 401) {
                    sessionStorage.removeItem('deployToken');
                    throw new Error('Invalid token. Please try again.');
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            this.showSuccess(result.message);
            this.closeConfigModal();
            
            // Refresh services list
            setTimeout(() => this.loadServices(), 1000);
            
        } catch (error) {
            console.error('Error saving config:', error);
            this.showError(`Failed to save configuration: ${error.message}`);
        }
    }
    
    async getToken() {
        // Check if token is already stored in session
        let token = sessionStorage.getItem('deployToken');
        
        if (!token) {
            // Show a modal instead of prompt for better UX
            token = await this.showTokenModal();
        }
        
        return token || '';
    }
    
    showTokenModal() {
        return new Promise((resolve) => {
            // Create modal overlay
            const overlay = document.createElement('div');
            overlay.className = 'token-modal-overlay';
            overlay.innerHTML = `
                <div class="token-modal">
                    <h3>🔐 Authentication Required</h3>
                    <p>Please enter your deployment token to continue:</p>
                    <input type="password" id="tokenInput" placeholder="Enter token..." />
                    <div class="token-modal-buttons">
                        <button onclick="this.submitToken()" class="btn btn-primary">Submit</button>
                        <button onclick="this.cancelToken()" class="btn btn-secondary">Cancel</button>
                    </div>
                </div>
            `;
            
            // Add styles
            overlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.7); z-index: 1000; display: flex;
                justify-content: center; align-items: center;
            `;
            
            const modal = overlay.querySelector('.token-modal');
            modal.style.cssText = `
                background: white; padding: 2rem; border-radius: 8px;
                min-width: 300px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            `;
            
            const input = overlay.querySelector('#tokenInput');
            input.style.cssText = `
                width: 100%; padding: 0.5rem; margin: 1rem 0;
                border: 1px solid #ddd; border-radius: 4px;
            `;
            
            document.body.appendChild(overlay);
            input.focus();
            
            // Handle submission
            window.submitToken = () => {
                const token = input.value.trim();
                if (token) {
                    sessionStorage.setItem('deployToken', token);
                    document.body.removeChild(overlay);
                    resolve(token);
                } else {
                    alert('Please enter a valid token');
                }
            };
            
            // Handle cancellation
            window.cancelToken = () => {
                document.body.removeChild(overlay);
                resolve('');
            };
            
            // Handle Enter key
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    window.submitToken();
                }
            });
        });
    }
    
    startAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        
        this.autoRefreshInterval = setInterval(() => {
            if (this.monitoringActive) {
                this.loadServices();
            }
        }, 30000); // 30 seconds
    }
    
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }
    
    showLoading(message = 'Loading...') {
        const spinner = document.getElementById('spinner');
        const spinnerText = document.querySelector('.spinner-text');
        
        if (spinnerText) {
            spinnerText.textContent = message;
        }
        
        spinner.classList.remove('hidden');
    }
    
    hideLoading() {
        const spinner = document.getElementById('spinner');
        spinner.classList.add('hidden');
    }
    
    showError(message) {
        this.showAlert(message, 'alert-error');
    }
    
    showSuccess(message) {
        this.showAlert(message, 'alert-success');
    }
    
    showAlert(message, className = 'alert-info') {
        // Create or update alert
        let alertEl = document.getElementById('tempAlert');
        if (!alertEl) {
            alertEl = document.createElement('div');
            alertEl.id = 'tempAlert';
            alertEl.style.position = 'fixed';
            alertEl.style.top = '20px';
            alertEl.style.right = '20px';
            alertEl.style.zIndex = '9999';
            alertEl.style.minWidth = '300px';
            document.body.appendChild(alertEl);
        }
        
        alertEl.className = `alert ${className}`;
        alertEl.textContent = message;
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            if (alertEl && alertEl.parentNode) {
                alertEl.parentNode.removeChild(alertEl);
            }
        }, 5000);
    }
}

// Global functions
let servicesMonitor;

function refreshServices() {
    if (servicesMonitor) {
        servicesMonitor.loadServices();
    }
}

function toggleMonitoring() {
    if (servicesMonitor) {
        servicesMonitor.toggleMonitoring();
    }
}

function showConfig() {
    if (servicesMonitor) {
        servicesMonitor.showConfig();
    }
}

function closeConfigModal() {
    if (servicesMonitor) {
        servicesMonitor.closeConfigModal();
    }
}

function saveConfig() {
    if (servicesMonitor) {
        servicesMonitor.saveConfig();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    servicesMonitor = new ServicesMonitor();
    
    // Add modal click outside to close
    const configModal = document.getElementById('configModal');
    if (configModal) {
        configModal.addEventListener('click', (e) => {
            if (e.target === configModal) {
                closeConfigModal();
            }
        });
    }
    
    // Add escape key to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modal = document.getElementById('configModal');
            if (modal && modal.classList.contains('show')) {
                closeConfigModal();
            }
        }
    });
});
