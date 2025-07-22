/**
 * Services Monitor - Dashboard JavaScript
 * Handles service status monitoring, dashboard updates, and UI interactions
 */

class ServicesMonitor {
    constructor() {
        this.services = [];
        this.refreshInterval = 30000; // 30 seconds
        this.isAutoRefreshEnabled = true;
        this.intervalId = null;
        this.init();
    }

    init() {
        console.log('🚀 Initializing Services Monitor...');
        this.loadServices();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('autoRefreshToggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                this.isAutoRefreshEnabled = e.target.checked;
                if (this.isAutoRefreshEnabled) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }

        // Manual refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshServices();
            });
        }

        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }
    }

    async loadServices() {
        try {
            console.log('📡 Loading services...');
            const response = await fetch('/api/services/status');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('✅ Services data loaded:', data);
            
            this.services = data;
            this.updateDashboard();
            this.updateLastUpdated();
            
        } catch (error) {
            console.error('❌ Failed to load services:', error);
            this.showError('Failed to load services: ' + error.message);
        }
    }

    async refreshServices() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '🔄 Refreshing...';
        }

        await this.loadServices();

        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '🔄 Refresh';
        }
    }

    updateDashboard() {
        this.updateServiceCards();
        this.updateSummaryStats();
    }

    updateServiceCards() {
        const container = document.getElementById('servicesContainer');
        if (!container) return;

        const localServices = this.services.local_services || [];
        const remoteServices = this.services.remote_services || [];
        const allServices = [...localServices, ...remoteServices];

        if (allServices.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-info">
                        <h5>📋 No Services Configured</h5>
                        <p>No services are currently configured for monitoring. Add services to your <code>services.json</code> file to get started.</p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = allServices.map(service => this.createServiceCard(service)).join('');
    }

    createServiceCard(service) {
        const statusClass = this.getStatusClass(service.status);
        const statusIcon = this.getStatusIcon(service.status);
        const serviceIcon = service.icon || '📦';
        const criticalBadge = service.critical ? '<span class="badge badge-danger">Critical</span>' : '';

        return `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card service-card ${statusClass}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0">
                                ${serviceIcon} ${service.name}
                            </h6>
                            <div>
                                ${criticalBadge}
                                <span class="status-badge ${statusClass}">
                                    ${statusIcon} ${service.status}
                                </span>
                            </div>
                        </div>
                        
                        ${service.description ? `<p class="card-text text-muted small">${service.description}</p>` : ''}
                        
                        <div class="service-details">
                            ${service.port ? `<small><strong>Port:</strong> ${service.port}</small><br>` : ''}
                            ${service.container_name ? `<small><strong>Container:</strong> ${service.container_name}</small><br>` : ''}
                            ${service.url ? `<small><strong>URL:</strong> <a href="${service.url}" target="_blank" class="text-primary">${service.url}</a></small><br>` : ''}
                            ${service.message ? `<small class="text-muted">${service.message}</small><br>` : ''}
                            ${service.timestamp ? `<small class="text-muted">Last check: ${this.formatTimestamp(service.timestamp)}</small>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    updateSummaryStats() {
        const summary = this.services.summary || {};
        
        this.updateStat('totalServices', summary.total_services || 0);
        this.updateStat('healthyServices', summary.healthy_services || 0);
        this.updateStat('unhealthyServices', summary.unhealthy_services || 0);
        this.updateStat('criticalDown', summary.critical_down || 0);
    }

    updateStat(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    getStatusClass(status) {
        const statusMap = {
            'healthy': 'status-healthy',
            'running': 'status-healthy',
            'unhealthy': 'status-warning',
            'stopped': 'status-warning',
            'error': 'status-error',
            'not_found': 'status-error',
            'unavailable': 'status-error'
        };
        return statusMap[status] || 'status-unknown';
    }

    getStatusIcon(status) {
        const iconMap = {
            'healthy': '✅',
            'running': '✅',
            'unhealthy': '⚠️',
            'stopped': '⏸️',
            'error': '❌',
            'not_found': '❌',
            'unavailable': '⚪'
        };
        return iconMap[status] || '❓';
    }

    formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString();
        } catch (e) {
            return timestamp;
        }
    }

    updateLastUpdated() {
        const element = document.getElementById('lastUpdated');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    }

    showError(message) {
        const container = document.getElementById('servicesContainer');
        if (container) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        <h5>❌ Error</h5>
                        <p>${message}</p>
                        <button class="btn btn-outline-danger btn-sm" onclick="servicesMonitor.refreshServices()">
                            🔄 Try Again
                        </button>
                    </div>
                </div>
            `;
        }
    }

    startAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        if (this.isAutoRefreshEnabled) {
            this.intervalId = setInterval(() => {
                this.loadServices();
            }, this.refreshInterval);
            console.log(`🔄 Auto-refresh started (${this.refreshInterval/1000}s interval)`);
        }
    }

    stopAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('⏹️ Auto-refresh stopped');
        }
    }

    async logout() {
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                console.log('✅ Logout successful');
                // Clear session and redirect
                window.location.href = '/login?message=Logged out successfully';
            } else {
                throw new Error('Logout failed');
            }
        } catch (error) {
            console.error('❌ Logout error:', error);
            alert('Failed to logout. Please try again.');
        }
    }
}

// Global instance
let servicesMonitor;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    servicesMonitor = new ServicesMonitor();
});

// Export for global access
window.servicesMonitor = servicesMonitor;
