// =================================
// Deploy Servers Page JavaScript
// =================================

// Global variables
let servers = [];
let selectedServer = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Deploy page loaded');
    loadServers();
    setupEventListeners();
});

function setupEventListeners() {
    // Setup form submission
    const deployForm = document.getElementById('deployForm');
    if (deployForm) {
        deployForm.addEventListener('submit', handleDeploySubmit);
    }
    
    // Setup refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadServers);
    }
}

function loadServers() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.textContent = '🔄 Loading...';
        refreshBtn.disabled = true;
    }
    
    showSpinner();
    
    fetch('/servers')
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        servers = data;
        displayServers(servers);
        
        if (refreshBtn) {
            refreshBtn.textContent = '🔄 Refresh Servers';
            refreshBtn.disabled = false;
        }
    })
    .catch(error => {
        hideSpinner();
        showStatus(`❌ Error loading servers: ${error.message}`, 'error');
        console.error('Server loading error:', error);
        
        if (refreshBtn) {
            refreshBtn.textContent = '🔄 Refresh Servers';
            refreshBtn.disabled = false;
        }
    });
}

function displayServers(serverList) {
    const serverContainer = document.getElementById('serverList');
    if (!serverContainer) return;
    
    if (serverList.length === 0) {
        serverContainer.innerHTML = '<p class="text-muted">No servers configured.</p>';
        return;
    }
    
    const serverCards = serverList.map(server => {
        const statusClass = getStatusClass(server.status);
        const statusIcon = getStatusIcon(server.status);
        
        return `
            <div class="server-card ${statusClass}" data-server="${server.ip}">
                <div class="server-header">
                    <h4>${server.name}</h4>
                    <span class="server-status">${statusIcon} ${server.status}</span>
                </div>
                <div class="server-details">
                    <p><strong>IP:</strong> ${server.ip}</p>
                    <p><strong>User:</strong> ${server.user}</p>
                    <p><strong>Type:</strong> ${server.type}</p>
                    <p><strong>Description:</strong> ${server.description}</p>
                    <p><strong>Path:</strong> ${server.path}</p>
                </div>
                <div class="server-actions">
                    <button onclick="selectServer('${server.ip}', '${server.name}')" 
                            class="btn btn-primary ${server.status === 'offline' ? 'disabled' : ''}">
                        🚀 Select for Deploy
                    </button>
                    <button onclick="testServerConnection('${server.ip}')" class="btn btn-info btn-sm">
                        🔍 Test Connection
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    serverContainer.innerHTML = serverCards;
}

function getStatusClass(status) {
    switch(status) {
        case 'online': return 'server-online';
        case 'offline': return 'server-offline';
        default: return 'server-unknown';
    }
}

function getStatusIcon(status) {
    switch(status) {
        case 'online': return '🟢';
        case 'offline': return '🔴';
        default: return '🟡';
    }
}

function selectServer(serverIp, serverName) {
    // Remove previous selection
    document.querySelectorAll('.server-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Add selection to current card
    const selectedCard = document.querySelector(`[data-server="${serverIp}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
    
    selectedServer = { ip: serverIp, name: serverName };
    
    // Update deploy form
    updateDeployForm(selectedServer);
    
    showStatus(`✅ Selected server: ${serverName} (${serverIp})`, 'success');
}

function updateDeployForm(server) {
    const deploySection = document.getElementById('deploySection');
    const selectedServerInfo = document.getElementById('selectedServerInfo');
    
    if (deploySection) {
        deploySection.classList.remove('hidden');
    }
    
    if (selectedServerInfo) {
        selectedServerInfo.innerHTML = `
            <div class="selected-server">
                <h4>🎯 Selected Server</h4>
                <p><strong>${server.name}</strong> (${server.ip})</p>
            </div>
        `;
    }
}

function testServerConnection(serverIp) {
    showStatus('🔍 Testing connection...', 'info');
    
    fetch('/api/health', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ target: serverIp })
    })
    .then(response => response.json())
    .then(data => {
        const isOnline = data.ping?.success || false;
        const message = isOnline ? 
            `✅ Server ${serverIp} is reachable` : 
            `❌ Server ${serverIp} is not reachable`;
        
        showStatus(message, isOnline ? 'success' : 'error');
    })
    .catch(error => {
        showStatus(`❌ Connection test failed: ${error.message}`, 'error');
        console.error('Connection test error:', error);
    });
}

function handleDeploySubmit(e) {
    e.preventDefault();
    
    if (!selectedServer) {
        showStatus('❌ Please select a server first', 'error');
        return;
    }
    
    const token = document.getElementById('deployToken').value.trim();
    if (!token) {
        showStatus('❌ Please enter deployment token', 'error');
        return;
    }
    
    triggerDeployment(selectedServer.ip, token);
}

function triggerDeployment(serverIp, token) {
    const deployBtn = document.getElementById('deployBtn');
    
    if (deployBtn) {
        deployBtn.textContent = '🚀 Deploying...';
        deployBtn.disabled = true;
    }
    
    showStatus('🚀 Triggering deployment...', 'info');
    showSpinner();
    
    fetch('/trigger', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            token: token,
            server: serverIp
        })
    })
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Redirect to result page
        const resultUrl = `/trigger-result?log=${data.log_file}&message=${encodeURIComponent(data.message)}`;
        window.location.href = resultUrl;
    })
    .catch(error => {
        hideSpinner();
        showStatus(`❌ Deployment failed: ${error.message}`, 'error');
        console.error('Deployment error:', error);
        
        if (deployBtn) {
            deployBtn.textContent = '🚀 Deploy Now';
            deployBtn.disabled = false;
        }
    });
}

// Quick deploy function (from URL params or direct call)
function quickDeploy(serverIp, token) {
    if (!serverIp || !token) {
        showStatus('❌ Missing server or token for quick deploy', 'error');
        return;
    }
    
    // Find server info
    const server = servers.find(s => s.ip === serverIp || s.alias === serverIp);
    if (server) {
        selectServer(server.ip, server.name);
        
        // Set token
        const tokenInput = document.getElementById('deployToken');
        if (tokenInput) {
            tokenInput.value = token;
        }
        
        // Auto trigger
        setTimeout(() => {
            triggerDeployment(server.ip, token);
        }, 1000);
    } else {
        showStatus(`❌ Server '${serverIp}' not found`, 'error');
    }
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

// Check for URL parameters on load
window.addEventListener('load', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const server = urlParams.get('server');
    const token = urlParams.get('token');
    
    if (server && token) {
        // Wait for servers to load first
        setTimeout(() => {
            quickDeploy(server, token);
        }, 2000);
    }
});
