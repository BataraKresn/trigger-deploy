// =================================
// Deploy Servers JavaScript Module
// =================================

class DeployManager {
    constructor() {
        this.servers = [];
        this.selectedServer = null;
        this.isLoading = false;
        this.init();
    }

    init() {
        // Load servers when page loads
        this.loadServers();
        
        // Setup event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('authModal');
            if (e.target === modal) {
                this.closeModal();
            }
        });

        // Handle ESC key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    async loadServers() {
        try {
            this.showLoading('Loading servers...');
            
            const response = await fetch('/servers');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.servers = await response.json();
            this.renderServerList();
            
        } catch (error) {
            console.error('Error loading servers:', error);
            this.showError(`Failed to load servers: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    renderServerList() {
        const container = document.getElementById('server-list');
        
        if (!this.servers || this.servers.length === 0) {
            container.innerHTML = `
                <div class="text-center p-3">
                    <div class="alert alert-warning">
                        <h4>📭 No Servers Found</h4>
                        <p>No servers are configured for deployment.</p>
                        <p class="text-muted">Please check your servers.json configuration.</p>
                    </div>
                </div>
            `;
            return;
        }

        const serversHtml = this.servers.map(server => `
            <div class="server-card" onclick="deployManager.selectServer('${server.ip || server.alias}', '${server.name}')">
                <div class="server-header">
                    <h4>🖥️ ${server.name}</h4>
                    <span class="server-status ${server.status || 'unknown'}">${this.getStatusIcon(server.status)}</span>
                </div>
                <div class="server-details">
                    <p><strong>IP:</strong> <code>${server.ip || 'N/A'}</code></p>
                    <p><strong>Type:</strong> ${server.type || 'Unknown'}</p>
                    ${server.description ? `<p class="text-muted">${server.description}</p>` : ''}
                </div>
                <div class="server-actions">
                    <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); deployManager.selectServer('${server.ip || server.alias}', '${server.name}')">
                        🚀 Deploy
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = serversHtml;
    }

    getStatusIcon(status) {
        const statusMap = {
            'online': '🟢 Online',
            'offline': '🔴 Offline', 
            'maintenance': '🟡 Maintenance',
            'unknown': '⚪ Unknown'
        };
        return statusMap[status] || '⚪ Unknown';
    }

    selectServer(serverIp, serverName) {
        console.log('selectServer called with:', serverIp, serverName);
        
        if (this.isLoading) return;
        
        this.selectedServer = {
            ip: serverIp,
            name: serverName
        };
        
        console.log('Selected server:', this.selectedServer);
        this.showAuthModal();
    }

    showAuthModal() {
        console.log('showAuthModal called');
        const modal = document.getElementById('authModal');
        const tokenInput = document.getElementById('deployTokenInput');
        
        if (!modal) {
            console.error('Auth modal not found!');
            return;
        }
        
        console.log('Showing modal...');
        modal.style.display = 'flex';
        
        // Focus on token input
        setTimeout(() => {
            if (tokenInput) {
                tokenInput.focus();
            }
        }, 100);
        
        // Clear previous token
        if (tokenInput) {
            tokenInput.value = '';
        }
    }

    closeModal() {
        const modal = document.getElementById('authModal');
        const tokenInput = document.getElementById('deployTokenInput');
        
        modal.style.display = 'none';
        tokenInput.value = '';
        this.selectedServer = null;
    }

    async submitDeploy() {
        const tokenInput = document.getElementById('deployTokenInput');
        const token = tokenInput.value.trim();
        
        if (!token) {
            this.showError('Please enter deployment token');
            tokenInput.focus();
            return;
        }

        if (!this.selectedServer) {
            this.showError('No server selected');
            this.closeModal();
            return;
        }

        try {
            this.showGlobalLoading('🚀 Triggering deployment...');
            this.closeModal();
            
            const response = await fetch('/trigger', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token: token,
                    server: this.selectedServer.ip
                })
            });

            const result = await response.json();
            
            if (!response.ok) {
                if (response.status === 403) {
                    // Invalid token - redirect to error page
                    window.location.href = '/invalid-token';
                    return;
                }
                throw new Error(result.error || `HTTP ${response.status}`);
            }

            // Success - show result
            this.showSuccess(`✅ Deployment triggered for ${this.selectedServer.name}`);
            
            // Redirect to result page after short delay
            setTimeout(() => {
                if (result.log_file) {
                    window.location.href = `/trigger-result?log=${encodeURIComponent(result.log_file)}&message=${encodeURIComponent('Deployment triggered successfully')}`;
                } else {
                    window.location.href = '/trigger-result';
                }
            }, 1500);
            
        } catch (error) {
            console.error('Deployment error:', error);
            this.showError(`❌ Deployment failed: ${error.message}`);
        } finally {
            this.hideGlobalLoading();
        }
    }

    showLoading(message = 'Loading...') {
        const container = document.getElementById('server-list');
        container.innerHTML = `
            <div class="text-center p-3">
                <div class="spinner"></div>
                <p class="mt-2 text-muted">${message}</p>
            </div>
        `;
    }

    hideLoading() {
        // Loading will be hidden when renderServerList is called
    }

    showGlobalLoading(message = 'Processing...') {
        const spinner = document.getElementById('spinner');
        const spinnerText = document.querySelector('.spinner-text');
        
        if (spinnerText) {
            spinnerText.textContent = message;
        }
        
        spinner.classList.remove('hidden');
        this.isLoading = true;
    }

    hideGlobalLoading() {
        const spinner = document.getElementById('spinner');
        spinner.classList.add('hidden');
        this.isLoading = false;
    }

    showError(message) {
        this.showStatus(message, 'alert-error');
    }

    showSuccess(message) {
        this.showStatus(message, 'alert-success');
    }

    showStatus(message, className = 'alert-info') {
        const statusEl = document.getElementById('status');
        statusEl.className = `alert ${className}`;
        statusEl.textContent = message;
        statusEl.classList.remove('hidden');
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            statusEl.classList.add('hidden');
        }, 5000);
    }
}

// Global functions for HTML onclick handlers
let deployManager;

function refreshServerList() {
    if (deployManager) {
        deployManager.loadServers();
    }
}

function closeModal() {
    if (deployManager) {
        deployManager.closeModal();
    }
}

function submitDeploy() {
    if (deployManager) {
        deployManager.submitDeploy();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    deployManager = new DeployManager();
});

// Handle form submission with Enter key
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('#authModal form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            submitDeploy();
        });
    }
});
