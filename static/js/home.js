// =================================
// Home Page JavaScript Functions
// =================================

// Global variables
let isHealthCheckVisible = false;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Home page loaded');
    loadInitialData();
});

function loadInitialData() {
    // Load any initial data if needed
    updateLastActivity();
}

function updateLastActivity() {
    const now = new Date().toLocaleString();
    const lastUpdateElement = document.getElementById('lastUpdate');
    if (lastUpdateElement) {
        lastUpdateElement.textContent = `Last updated: ${now}`;
    }
}

// Health Check Functions
function showHealthInput() {
    const container = document.getElementById('healthInputContainer');
    const btn = document.getElementById('healthBtn');
    
    if (container && btn) {
        container.classList.remove('hidden');
        btn.textContent = '💗 Health Check Active';
        btn.disabled = true;
        isHealthCheckVisible = true;
        
        // Focus on input
        const input = document.getElementById('healthTarget');
        if (input) input.focus();
    }
}

function cancelHealthCheck() {
    const container = document.getElementById('healthInputContainer');
    const btn = document.getElementById('healthBtn');
    const input = document.getElementById('healthTarget');
    
    if (container && btn) {
        container.classList.add('hidden');
        btn.textContent = '💗 Check Health';
        btn.disabled = false;
        isHealthCheckVisible = false;
        
        if (input) input.value = '';
        hideStatus();
        hideHealthStatus();
    }
}

function executeHealthCheck() {
    const target = document.getElementById('healthTarget').value.trim() || 'google.co.id';
    
    showStatus('🔍 Performing health check...', 'info');
    showSpinner();
    
    fetch('/api/health', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ target: target })
    })
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        displayHealthResults(data);
        cancelHealthCheck();
    })
    .catch(error => {
        hideSpinner();
        showStatus(`❌ Error: ${error.message}`, 'error');
        console.error('Health check error:', error);
    });
}

function displayHealthResults(data) {
    const healthStatus = document.getElementById('healthStatus');
    const healthContent = document.getElementById('healthContent');
    
    if (!healthStatus || !healthContent) return;
    
    healthStatus.classList.remove('hidden');
    
    const pingStatus = data.ping?.success ? '✅' : '❌';
    const dnsStatus = data.dns?.success ? '✅' : '❌';
    const httpStatus = data.http?.success ? '✅' : '❌';
    
    healthContent.innerHTML = `
        <div class="health-grid">
            <div class="health-card">
                <h4>${pingStatus} Ping Test</h4>
                <p>${data.ping?.message || 'No data'}</p>
                <small>${data.ping?.details || ''}</small>
            </div>
            <div class="health-card">
                <h4>${dnsStatus} DNS Resolution</h4>
                <p>${data.dns?.message || 'No data'}</p>
                <small>IP: ${data.dns?.ip || 'N/A'}</small>
            </div>
            <div class="health-card">
                <h4>${httpStatus} HTTP Check</h4>
                <p>${data.http?.message || 'No data'}</p>
                <small>Response time: ${data.http?.response_time ? (data.http.response_time * 1000).toFixed(0) + 'ms' : 'N/A'}</small>
            </div>
        </div>
        <div class="mt-3">
            <p><strong>Target:</strong> ${data.target}</p>
            <p><strong>Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}</p>
        </div>
    `;
}

// Log Functions
function loadLogList() {
    const logBtn = document.getElementById('logBtn');
    const logListBox = document.getElementById('logListBox');
    
    if (logBtn) {
        logBtn.textContent = '📁 Loading...';
        logBtn.disabled = true;
    }
    
    showSpinner();
    
    fetch('/api/logs/list')
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        displayLogList(data.logs || []);
        
        if (logBtn) {
            logBtn.textContent = '📁 Browse Logs';
            logBtn.disabled = false;
        }
        
        if (logListBox) {
            logListBox.classList.remove('hidden');
        }
    })
    .catch(error => {
        hideSpinner();
        showStatus(`❌ Error loading logs: ${error.message}`, 'error');
        console.error('Log loading error:', error);
        
        if (logBtn) {
            logBtn.textContent = '📁 Browse Logs';
            logBtn.disabled = false;
        }
    });
}

function displayLogList(logs) {
    const logList = document.getElementById('logList');
    if (!logList) return;
    
    if (logs.length === 0) {
        logList.innerHTML = '<p class="text-muted">No log files found.</p>';
        return;
    }
    
    const logItems = logs.map(log => `
        <div class="log-item">
            <div class="log-info">
                <strong>${log.name}</strong>
                <span class="log-meta">
                    ${log.size} | ${new Date(log.modified).toLocaleString()}
                </span>
            </div>
            <div class="log-actions">
                <button onclick="viewLog('${log.name}')" class="btn btn-sm btn-info">
                    👁️ View
                </button>
                <button onclick="downloadLog('${log.name}')" class="btn btn-sm btn-secondary">
                    💾 Download
                </button>
            </div>
        </div>
    `).join('');
    
    logList.innerHTML = logItems;
}

function viewLog(logName) {
    showSpinner();
    
    fetch(`/logs/${logName}`)
    .then(response => response.text())
    .then(content => {
        hideSpinner();
        displayLogContent(logName, content);
    })
    .catch(error => {
        hideSpinner();
        showStatus(`❌ Error loading log: ${error.message}`, 'error');
        console.error('Log view error:', error);
    });
}

function displayLogContent(logName, content) {
    const logOutput = document.getElementById('logOutput');
    if (!logOutput) return;
    
    logOutput.innerHTML = `
        <div class="log-header">
            <h3>📄 ${logName}</h3>
            <button onclick="hideLogOutput()" class="btn btn-sm btn-secondary">✖️ Close</button>
        </div>
        <pre class="log-content">${escapeHtml(content)}</pre>
    `;
    
    logOutput.classList.remove('hidden');
    logOutput.scrollIntoView({ behavior: 'smooth' });
}

function hideLogOutput() {
    const logOutput = document.getElementById('logOutput');
    if (logOutput) {
        logOutput.classList.add('hidden');
    }
}

function downloadLog(logName) {
    window.open(`/logs/${logName}`, '_blank');
}

// Utility Functions
function showStatus(message, type = 'info') {
    const status = document.getElementById('status');
    if (!status) return;
    
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

function hideHealthStatus() {
    const healthStatus = document.getElementById('healthStatus');
    if (healthStatus) {
        healthStatus.classList.add('hidden');
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

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // ESC to cancel health check
    if (e.key === 'Escape' && isHealthCheckVisible) {
        cancelHealthCheck();
    }
    
    // Enter to execute health check
    if (e.key === 'Enter' && isHealthCheckVisible) {
        executeHealthCheck();
    }
});
