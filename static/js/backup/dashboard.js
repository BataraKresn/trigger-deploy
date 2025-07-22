// Dashboard-specific JavaScript functionality
class Dashboard {
    constructor() {
        this.autoRefreshInterval = null;
        this.refreshRate = 30000; // 30 seconds
        this.init();
    }

    init() {
        this.checkAuthenticationStatus();
        this.loadDashboardData();
        this.setupEventListeners();
        this.loadUserSettings();
        this.startAutoRefresh();
    }

    // Authentication check
    checkAuthenticationStatus() {
        const token = localStorage.getItem('authToken');
        const user = localStorage.getItem('userData');
        
        if (!token || !user) {
            window.location.href = '/login';
            return false;
        }

        try {
            const userData = JSON.parse(user);
            this.updateUserDisplay(userData);
            return true;
        } catch (error) {
            console.error('Invalid user data:', error);
            this.logout();
            return false;
        }
    }

    // Update user display in navigation
    updateUserDisplay(userData) {
        const userAvatar = document.querySelector('.user-avatar');
        const profileName = document.getElementById('profileName');
        const profileRole = document.getElementById('profileRole');
        const userNameSpan = document.querySelector('.user-details h4');
        const userRoleSpan = document.querySelector('.user-details span');

        if (userAvatar && userData.name) {
            userAvatar.textContent = userData.name.charAt(0).toUpperCase();
        }

        if (profileName) profileName.textContent = userData.name || 'User';
        if (profileRole) profileRole.textContent = userData.role || 'admin';
        if (userNameSpan) userNameSpan.textContent = userData.name || 'User';
        if (userRoleSpan) userRoleSpan.textContent = userData.role || 'admin';
    }

    // Load dashboard statistics and data
    async loadDashboardData() {
        try {
            await Promise.all([
                this.loadStatistics(),
                this.loadRecentActivity()
            ]);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showAlert('Failed to load dashboard data', 'error');
        }
    }

    // Load statistics for dashboard cards
    async loadStatistics() {
        try {
            const response = await fetch('/api/stats', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (response.ok) {
                const stats = await response.json();
                this.updateStatistics(stats);
            } else {
                // Fallback with placeholder data
                this.updateStatistics({
                    totalDeployments: '0',
                    successfulDeployments: '0',
                    activeServers: '0',
                    runningServices: '0'
                });
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
            // Show placeholder data
            this.updateStatistics({
                totalDeployments: '-',
                successfulDeployments: '-',
                activeServers: '-',
                runningServices: '-'
            });
        }
    }

    // Update statistics in the UI
    updateStatistics(stats) {
        const elements = {
            totalDeployments: document.getElementById('totalDeployments'),
            successfulDeployments: document.getElementById('successfulDeployments'),
            activeServers: document.getElementById('activeServers'),
            runningServices: document.getElementById('runningServices')
        };

        Object.keys(elements).forEach(key => {
            if (elements[key] && stats[key] !== undefined) {
                elements[key].textContent = stats[key];
            }
        });
    }

    // Load recent activity
    async loadRecentActivity() {
        try {
            const response = await fetch('/api/recent-activity', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
                }
            });

            if (response.ok) {
                const activities = await response.json();
                this.displayRecentActivity(activities);
            } else {
                this.displayRecentActivity([]);
            }
        } catch (error) {
            console.error('Error loading recent activity:', error);
            this.displayRecentActivity([]);
        }
    }

    // Display recent activity
    displayRecentActivity(activities) {
        const container = document.getElementById('recentActivity');
        if (!container) return;

        if (activities.length === 0) {
            container.innerHTML = `
                <div class="activity-item">
                    <div class="activity-icon info">📋</div>
                    <div class="activity-content">
                        <div class="activity-title">No recent activity</div>
                        <div class="activity-description">Start deploying to see activity here</div>
                    </div>
                    <div class="activity-time">-</div>
                </div>
            `;
            return;
        }

        const activityHTML = activities.map(activity => {
            const iconClass = this.getActivityIconClass(activity.type);
            const icon = this.getActivityIcon(activity.type);
            const timeAgo = this.getTimeAgo(activity.timestamp);

            return `
                <div class="activity-item">
                    <div class="activity-icon ${iconClass}">${icon}</div>
                    <div class="activity-content">
                        <div class="activity-title">${activity.title}</div>
                        <div class="activity-description">${activity.description}</div>
                    </div>
                    <div class="activity-time">${timeAgo}</div>
                </div>
            `;
        }).join('');

        container.innerHTML = activityHTML;
    }

    // Get activity icon class based on type
    getActivityIconClass(type) {
        const iconMap = {
            'success': 'success',
            'error': 'error',
            'deployment': 'info',
            'health': 'info',
            'service': 'info'
        };
        return iconMap[type] || 'info';
    }

    // Get activity icon based on type
    getActivityIcon(type) {
        const iconMap = {
            'success': '✅',
            'error': '❌',
            'deployment': '🚀',
            'health': '💗',
            'service': '🐳'
        };
        return iconMap[type] || '📋';
    }

    // Get time ago string
    getTimeAgo(timestamp) {
        try {
            const now = new Date();
            const time = new Date(timestamp);
            const diffMs = now - time;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMins / 60);
            const diffDays = Math.floor(diffHours / 24);

            if (diffMins < 1) return 'just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffHours < 24) return `${diffHours}h ago`;
            if (diffDays < 7) return `${diffDays}d ago`;
            return time.toLocaleDateString();
        } catch (error) {
            return 'unknown';
        }
    }

    // Setup event listeners
    setupEventListeners() {
        // User menu toggle
        const userInfo = document.querySelector('.user-info');
        if (userInfo) {
            userInfo.addEventListener('click', () => this.openUserMenu());
        }

        // Settings toggles
        const darkModeToggle = document.getElementById('darkModeToggle');
        const notificationsToggle = document.getElementById('notificationsToggle');
        const autoRefreshToggle = document.getElementById('autoRefreshToggle');

        if (darkModeToggle) {
            darkModeToggle.addEventListener('change', (e) => {
                this.toggleDarkMode(e.target.checked);
            });
        }

        if (notificationsToggle) {
            notificationsToggle.addEventListener('change', (e) => {
                this.toggleNotifications(e.target.checked);
            });
        }

        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                this.toggleAutoRefresh(e.target.checked);
            });
        }

        // Modal close events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeUserMenu();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeUserMenu();
                this.cancelHealthCheck();
            }
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.refreshDashboard();
            }
        });
    }

    // User menu functions
    openUserMenu() {
        const modal = document.getElementById('userMenuModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    closeUserMenu() {
        const modal = document.getElementById('userMenuModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    // User settings functions
    loadUserSettings() {
        const settings = JSON.parse(localStorage.getItem('userSettings') || '{}');
        
        const darkModeToggle = document.getElementById('darkModeToggle');
        const notificationsToggle = document.getElementById('notificationsToggle');
        const autoRefreshToggle = document.getElementById('autoRefreshToggle');

        if (darkModeToggle) darkModeToggle.checked = settings.darkMode || false;
        if (notificationsToggle) notificationsToggle.checked = settings.notifications !== false;
        if (autoRefreshToggle) autoRefreshToggle.checked = settings.autoRefresh !== false;

        // Apply dark mode if enabled
        if (settings.darkMode) {
            document.body.classList.add('dark-mode');
        }

        // Set auto refresh
        if (settings.autoRefresh === false) {
            this.stopAutoRefresh();
        }
    }

    saveUserSettings() {
        const settings = {
            darkMode: document.getElementById('darkModeToggle')?.checked || false,
            notifications: document.getElementById('notificationsToggle')?.checked || true,
            autoRefresh: document.getElementById('autoRefreshToggle')?.checked || true
        };

        localStorage.setItem('userSettings', JSON.stringify(settings));
        this.showAlert('Settings saved successfully', 'success');
        this.closeUserMenu();
    }

    toggleDarkMode(enabled) {
        if (enabled) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }

    toggleNotifications(enabled) {
        // Store notification preference
        console.log('Notifications:', enabled ? 'enabled' : 'disabled');
    }

    toggleAutoRefresh(enabled) {
        if (enabled) {
            this.startAutoRefresh();
        } else {
            this.stopAutoRefresh();
        }
    }

    // Auto refresh functionality
    startAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }

        this.autoRefreshInterval = setInterval(() => {
            this.refreshDashboard();
        }, this.refreshRate);
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    async refreshDashboard() {
        try {
            await this.loadDashboardData();
            console.log('Dashboard refreshed');
        } catch (error) {
            console.error('Failed to refresh dashboard:', error);
        }
    }

    // Logout function
    logout() {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');
        localStorage.removeItem('userSettings');
        this.stopAutoRefresh();
        window.location.href = '/login';
    }

    // Utility function to show alerts
    showAlert(message, type = 'info') {
        const statusElement = document.getElementById('status');
        if (!statusElement) return;

        statusElement.className = `alert alert-${type}`;
        statusElement.textContent = message;
        statusElement.classList.remove('hidden');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            statusElement.classList.add('hidden');
        }, 5000);
    }
}

// Health check functions (from original home.js)
function showHealthInput() {
    const container = document.getElementById('healthInputContainer');
    if (container) {
        container.classList.remove('hidden');
        document.getElementById('healthTarget')?.focus();
    }
}

function cancelHealthCheck() {
    const container = document.getElementById('healthInputContainer');
    if (container) {
        container.classList.add('hidden');
        document.getElementById('healthTarget').value = '';
    }
    
    const healthStatus = document.getElementById('healthStatus');
    if (healthStatus) {
        healthStatus.classList.add('hidden');
    }
}

async function executeHealthCheck() {
    const target = document.getElementById('healthTarget').value.trim() || 'google.co.id';
    const statusElement = document.getElementById('status');
    const healthContent = document.getElementById('healthContent');
    const healthStatus = document.getElementById('healthStatus');

    try {
        statusElement.className = 'alert alert-info';
        statusElement.textContent = `🔍 Checking health for: ${target}...`;
        statusElement.classList.remove('hidden');

        const response = await fetch('/api/health', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({ target: target })
        });

        const result = await response.json();

        if (response.ok) {
            statusElement.className = 'alert alert-success';
            statusElement.textContent = '✅ Health check completed successfully!';
            
            healthContent.textContent = result.output || 'Health check completed';
            healthStatus.classList.remove('hidden');
        } else {
            statusElement.className = 'alert alert-error';
            statusElement.textContent = `❌ Health check failed: ${result.error || 'Unknown error'}`;
        }
    } catch (error) {
        console.error('Health check error:', error);
        statusElement.className = 'alert alert-error';
        statusElement.textContent = `❌ Health check failed: ${error.message}`;
    }

    // Hide status after 5 seconds
    setTimeout(() => {
        statusElement.classList.add('hidden');
    }, 5000);
}

// Log functions (from original home.js)
async function loadLogList() {
    const statusElement = document.getElementById('status');
    const logListBox = document.getElementById('logListBox');
    const logList = document.getElementById('logList');

    try {
        statusElement.className = 'alert alert-info';
        statusElement.textContent = '📁 Loading log list...';
        statusElement.classList.remove('hidden');

        const response = await fetch('/api/logs', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        const data = await response.json();

        if (response.ok) {
            if (data.logs && data.logs.length > 0) {
                const logHTML = data.logs.map(log => 
                    `<div class="log-item" onclick="loadLogContent('${log}')">
                        📄 ${log}
                    </div>`
                ).join('');
                
                logList.innerHTML = logHTML;
                logListBox.classList.remove('hidden');
                
                statusElement.className = 'alert alert-success';
                statusElement.textContent = `📁 Found ${data.logs.length} log files`;
            } else {
                statusElement.className = 'alert alert-info';
                statusElement.textContent = '📁 No log files found';
            }
        } else {
            statusElement.className = 'alert alert-error';
            statusElement.textContent = `❌ Failed to load logs: ${data.error}`;
        }
    } catch (error) {
        console.error('Error loading logs:', error);
        statusElement.className = 'alert alert-error';
        statusElement.textContent = `❌ Error loading logs: ${error.message}`;
    }

    setTimeout(() => {
        statusElement.classList.add('hidden');
    }, 3000);
}

async function loadLogContent(filename) {
    const statusElement = document.getElementById('status');
    const logOutput = document.getElementById('logOutput');

    try {
        statusElement.className = 'alert alert-info';
        statusElement.textContent = `📖 Loading ${filename}...`;
        statusElement.classList.remove('hidden');

        const response = await fetch(`/api/logs/${filename}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        const data = await response.json();

        if (response.ok) {
            logOutput.textContent = data.content;
            logOutput.classList.remove('hidden');
            
            statusElement.className = 'alert alert-success';
            statusElement.textContent = `📖 Loaded ${filename}`;
        } else {
            statusElement.className = 'alert alert-error';
            statusElement.textContent = `❌ Failed to load ${filename}: ${data.error}`;
        }
    } catch (error) {
        console.error('Error loading log content:', error);
        statusElement.className = 'alert alert-error';
        statusElement.textContent = `❌ Error loading log: ${error.message}`;
    }

    setTimeout(() => {
        statusElement.classList.add('hidden');
    }, 3000);
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

// Global functions for modal management
window.openUserMenu = () => window.dashboard?.openUserMenu();
window.closeUserMenu = () => window.dashboard?.closeUserMenu();
window.saveUserSettings = () => window.dashboard?.saveUserSettings();
window.logout = () => window.dashboard?.logout();
