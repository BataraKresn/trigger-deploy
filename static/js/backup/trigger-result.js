// =================================
// Trigger Result Page JavaScript
// =================================

// Global variables
let logRefreshInterval = null;
let isAutoRefresh = true;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Trigger Result page loaded');
    
    // Get parameters from URL
    const urlParams = new URLSearchParams(window.location.search);
    const logFile = urlParams.get('log');
    const message = urlParams.get('message');
    
    if (logFile) {
        startLogMonitoring(logFile);
    }
    
    if (message) {
        showInitialMessage(message);
    }
    
    setupEventListeners();
});

function setupEventListeners() {
    const refreshBtn = document.getElementById('refreshLogBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            const urlParams = new URLSearchParams(window.location.search);
            const logFile = urlParams.get('log');
            if (logFile) {
                loadLogContent(logFile);
            }
        });
    }
    
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', toggleAutoRefresh);
    }
    
    const downloadBtn = document.getElementById('downloadLogBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadLog);
    }
}

function showInitialMessage(message) {
    const messageContainer = document.getElementById('deploymentMessage');
    if (messageContainer) {
        messageContainer.innerHTML = `
            <div class="alert alert-info">
                <h3>🚀 Deployment Status</h3>
                <p>${decodeURIComponent(message)}</p>
            </div>
        `;
    }
}

function startLogMonitoring(logFile) {
    // Load initial content
    loadLogContent(logFile);
    
    // Set up auto-refresh
    logRefreshInterval = setInterval(() => {
        if (isAutoRefresh) {
            loadLogContent(logFile, true); // Silent refresh
        }
    }, 3000); // Refresh every 3 seconds
}

function loadLogContent(logFile, isSilent = false) {
    if (!isSilent) {
        showStatus('📄 Loading log content...', 'info');
    }
    
    fetch(`/logs/${logFile}`)
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.text();
    })
    .then(content => {
        displayLogContent(content, logFile);
        
        if (!isSilent) {
            hideStatus();
        }
        
        updateLastRefresh();
        
        // Check if deployment is complete
        checkDeploymentStatus(content);
    })
    .catch(error => {
        if (!isSilent) {
            showStatus(`❌ Error loading log: ${error.message}`, 'error');
        }
        console.error('Log loading error:', error);
    });
}

function displayLogContent(content, logFile) {
    const logContainer = document.getElementById('logContent');
    const logHeader = document.getElementById('logHeader');
    
    if (logHeader) {
        logHeader.innerHTML = `
            <h3>📄 Deployment Log: ${logFile}</h3>
            <div class="log-controls">
                <button id="refreshLogBtn" class="btn btn-sm btn-secondary">🔄 Refresh</button>
                <button id="downloadLogBtn" class="btn btn-sm btn-info">💾 Download</button>
                <label class="auto-refresh-label">
                    <input type="checkbox" id="autoRefreshToggle" ${isAutoRefresh ? 'checked' : ''}> 
                    Auto-refresh
                </label>
            </div>
        `;
        
        // Re-attach event listeners after updating header
        setupEventListeners();
    }
    
    if (logContainer) {
        // Process log content to highlight important lines
        const processedContent = processLogContent(content);
        logContainer.innerHTML = `<pre class="log-output">${processedContent}</pre>`;
        
        // Auto-scroll to bottom
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

function processLogContent(content) {
    if (!content) return 'No log content available.';
    
    // Escape HTML
    const escaped = escapeHtml(content);
    
    // Highlight different types of log lines
    return escaped
        .split('\n')
        .map(line => {
            if (line.includes('🚀') || line.includes('Deploy trigger received')) {
                return `<span class="log-info">${line}</span>`;
            } else if (line.includes('✅') || line.includes('SUCCESS') || line.includes('completed successfully')) {
                return `<span class="log-success">${line}</span>`;
            } else if (line.includes('❌') || line.includes('ERROR') || line.includes('FAILED') || line.includes('failed')) {
                return `<span class="log-error">${line}</span>`;
            } else if (line.includes('⚠️') || line.includes('WARNING') || line.includes('WARN')) {
                return `<span class="log-warning">${line}</span>`;
            } else if (line.includes('[') && line.includes(']') && line.includes(':')) {
                return `<span class="log-timestamp">${line}</span>`;
            } else {
                return line;
            }
        })
        .join('\n');
}

function checkDeploymentStatus(content) {
    const statusIndicator = document.getElementById('deploymentStatus');
    
    if (!statusIndicator) return;
    
    if (content.includes('completed successfully') || content.includes('✅')) {
        statusIndicator.innerHTML = `
            <div class="alert alert-success">
                <h4>✅ Deployment Completed Successfully</h4>
                <p>The deployment has finished successfully.</p>
            </div>
        `;
        
        // Stop auto-refresh for completed deployments
        if (isAutoRefresh) {
            toggleAutoRefresh({ target: { checked: false } });
        }
        
    } else if (content.includes('failed') || content.includes('❌') || content.includes('ERROR')) {
        statusIndicator.innerHTML = `
            <div class="alert alert-danger">
                <h4>❌ Deployment Failed</h4>
                <p>The deployment encountered an error. Check the log for details.</p>
            </div>
        `;
        
        // Stop auto-refresh for failed deployments
        if (isAutoRefresh) {
            toggleAutoRefresh({ target: { checked: false } });
        }
        
    } else {
        statusIndicator.innerHTML = `
            <div class="alert alert-info">
                <h4>🔄 Deployment In Progress</h4>
                <p>The deployment is currently running. Please wait...</p>
            </div>
        `;
    }
}

function toggleAutoRefresh(e) {
    isAutoRefresh = e.target.checked;
    const status = isAutoRefresh ? 'enabled' : 'disabled';
    showStatus(`🔄 Auto-refresh ${status}`, 'info');
    
    if (!isAutoRefresh && logRefreshInterval) {
        // Don't clear interval, just stop refreshing
        console.log('Auto-refresh paused');
    }
}

function downloadLog() {
    const urlParams = new URLSearchParams(window.location.search);
    const logFile = urlParams.get('log');
    
    if (logFile) {
        // Create download link
        const link = document.createElement('a');
        link.href = `/logs/${logFile}`;
        link.download = logFile;
        link.target = '_blank';
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showStatus('💾 Download started', 'success');
    } else {
        showStatus('❌ No log file to download', 'error');
    }
}

function updateLastRefresh() {
    const lastRefreshElement = document.getElementById('lastRefresh');
    if (lastRefreshElement) {
        lastRefreshElement.textContent = `Last updated: ${new Date().toLocaleString()}`;
    }
}

// Navigation functions
function goHome() {
    window.location.href = '/';
}

function goToMetrics() {
    window.location.href = '/metrics';
}

function viewDeploymentHistory() {
    window.location.href = '/metrics#deployment-history';
}

// Utility Functions
function showStatus(message, type = 'info') {
    const status = document.getElementById('status');
    if (!status) return;
    
    status.className = `alert alert-${type}`;
    status.textContent = message;
    status.classList.remove('hidden');
    
    // Auto hide after 3 seconds for non-error messages
    if (type !== 'error') {
        setTimeout(() => hideStatus(), 3000);
    }
}

function hideStatus() {
    const status = document.getElementById('status');
    if (status) {
        status.classList.add('hidden');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (logRefreshInterval) {
        clearInterval(logRefreshInterval);
    }
});

// Handle page visibility change to pause/resume auto-refresh
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause auto-refresh
        console.log('Page hidden, pausing auto-refresh');
    } else {
        // Page is visible, resume auto-refresh if enabled
        if (isAutoRefresh) {
            console.log('Page visible, resuming auto-refresh');
            const urlParams = new URLSearchParams(window.location.search);
            const logFile = urlParams.get('log');
            if (logFile) {
                loadLogContent(logFile, true);
            }
        }
    }
});
