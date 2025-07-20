/**
 * 🏠 Home Page JavaScript
 * Trigger Deploy Platform
 */

// Global variables
let eventSource = null;
let currentViewedLog = null;

/**
 * 🏥 Health Check Functions
 */
function showHealthInput() {
  const container = document.getElementById("healthInputContainer");
  const btn = document.getElementById("healthBtn");
  
  hideAllDisplays();
  container.classList.remove("hidden");
  btn.textContent = "🔄 Checking Health...";
  btn.disabled = true;
  
  // Focus on input
  document.getElementById("healthTarget").focus();
}

function cancelHealthCheck() {
  const container = document.getElementById("healthInputContainer");
  const btn = document.getElementById("healthBtn");
  const input = document.getElementById("healthTarget");
  
  container.classList.add("hidden");
  btn.textContent = "💗 Check Health";
  btn.onclick = showHealthInput;
  btn.disabled = false;
  input.value = "";
}

function hideHealthResults() {
  const el = document.getElementById("healthStatus");
  const btn = document.getElementById("healthBtn");
  
  el.classList.add("hidden");
  btn.textContent = "💗 Check Health";
  btn.onclick = showHealthInput;
  btn.disabled = false;
}

function executeHealthCheck() {
  const el = document.getElementById("healthStatus");
  const btn = document.getElementById("healthBtn");
  const container = document.getElementById("healthInputContainer");
  const target = document.getElementById("healthTarget").value || "google.co.id";

  // Hide input container and show results
  container.classList.add("hidden");
  el.classList.remove("hidden");

  btn.textContent = "⏳ Checking...";
  btn.disabled = true;

  showSpinner(el);

  fetch(`/health?target=${encodeURIComponent(target)}`)
    .then(res => res.json())
    .then(data => {
      btn.textContent = "❌ Hide Health";
      btn.onclick = hideHealthResults;
      btn.disabled = false;
      
      const healthContent = document.getElementById("healthContent");
      healthContent.innerHTML = `
        <div class="health-item ${data.resolve.includes('❌') ? 'error' : 'success'}">
          <div class="health-icon">🌐</div>
          <div class="health-content">
            <h4>DNS Resolution</h4>
            <p><strong>Target:</strong> ${data.target}</p>
            <p>${data.resolve}</p>
          </div>
        </div>
        <div class="health-item ${data.ping.includes('❌') ? 'error' : 'success'}">
          <div class="health-icon">📡</div>
          <div class="health-content">
            <h4>Network Connectivity</h4>
            <p>${data.ping}</p>
          </div>
        </div>
        <div class="health-item ${data.http.includes('❌') ? 'error' : 'success'}">
          <div class="health-icon">🌍</div>
          <div class="health-content">
            <h4>HTTP Response</h4>
            <p>${data.http}</p>
          </div>
        </div>
      `;
    })
    .catch(err => {
      btn.textContent = "💗 Check Health";
      btn.onclick = showHealthInput;
      btn.disabled = false;
      el.innerHTML = `
        <div class="health-item error">
          <div class="health-icon">❌</div>
          <div class="health-content">
            <h4>Health Check Failed</h4>
            <p>Error: ${err.message}</p>
          </div>
        </div>
      `;
      console.error("Health check failed:", err.message);
    });
}

// Legacy function for backward compatibility  
function checkHealth() {
  showHealthInput();
}

/**
 * 📁 Log Management Functions
 */
function loadLogList() {
  const logBox = document.getElementById('logListBox');
  const btn = document.getElementById('logBtn');

  if (!logBox.classList.contains('hidden')) {
    hideAllDisplays();
    btn.textContent = "📁 Browse Logs";
    return;
  }

  hideAllDisplays();
  logBox.classList.remove("hidden");
  btn.textContent = "❌ Hide Logs";

  showSpinner(document.getElementById("logList"));

  fetch('/logs')
    .then(res => res.json())
    .then(logs => {
      const listBox = document.getElementById("logList");
      
      if (logs.length === 0) {
        listBox.innerHTML = `
          <div class="alert alert-info">
            📝 No deployment logs found yet.
          </div>
        `;
        return;
      }

      listBox.innerHTML = logs.map(log => `
        <div class="log-item">
          <div>
            <a href="#" onclick="viewLogFile('${log}'); return false;">
              📄 ${log}
            </a>
            <small class="text-muted"> - ${formatLogDate(log)}</small>
          </div>
          <button class="btn btn-small btn-secondary" onclick="downloadLog('${log}')">
            ⬇️ Download
          </button>
        </div>
      `).join('');
    })
    .catch(err => {
      const listBox = document.getElementById("logList");
      listBox.innerHTML = `
        <div class="alert alert-error">
          ❌ Failed to load logs: ${err.message}
        </div>
      `;
    });
}

function viewLogFile(filename) {
  const output = document.getElementById("logOutput");
  const logBox = document.getElementById("logListBox");
  
  if (currentViewedLog === filename && !output.classList.contains("hidden")) {
    output.classList.add("hidden");
    output.textContent = "";
    currentViewedLog = null;
    return;
  }

  // Hide log list but keep output visible
  logBox.classList.add("hidden");
  output.classList.remove("hidden");
  currentViewedLog = filename;

  output.textContent = "⏳ Loading log file...";

  fetch(`/logs/${filename}`)
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.text();
    })
    .then(text => {
      output.textContent = text || "📝 Log file is empty.";
      
      // Add a back button
      const backBtn = document.createElement('div');
      backBtn.innerHTML = `
        <button class="btn btn-secondary mt-2" onclick="goBackToLogList()">
          ← Back to Log List
        </button>
      `;
      output.parentNode.insertBefore(backBtn, output.nextSibling);
    })
    .catch(err => {
      output.textContent = `❌ Error loading log: ${err.message}`;
    });
}

function downloadLog(filename) {
  const link = document.createElement('a');
  link.href = `/logs/${filename}`;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function goBackToLogList() {
  document.getElementById("logOutput").classList.add("hidden");
  document.getElementById("logListBox").classList.remove("hidden");
  
  // Remove back button
  const backBtn = document.querySelector('.btn.btn-secondary.mt-2');
  if (backBtn && backBtn.parentNode) {
    backBtn.parentNode.remove();
  }
  
  currentViewedLog = null;
}

/**
 * 🛠️ Utility Functions
 */
function hideAllDisplays() {
  document.getElementById("healthStatus").classList.add("hidden");
  document.getElementById("logOutput").classList.add("hidden");
  document.getElementById("logListBox").classList.add("hidden");
  document.getElementById("status").classList.add("hidden");
  
  // Reset button texts
  document.getElementById("healthBtn").textContent = "💗 Check Health";
  document.getElementById("logBtn").textContent = "📁 Browse Logs";
  
  // Close event source if open
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
}

function showSpinner(element) {
  element.innerHTML = `
    <div class="text-center p-3">
      <div class="spinner"></div>
      <p class="mt-2 text-muted">Loading...</p>
    </div>
  `;
}

function formatLogDate(filename) {
  // Extract date from filename like "trigger-20250719-234154.log"
  const match = filename.match(/trigger-(\d{8})-(\d{6})\.log/);
  if (!match) return "Unknown date";
  
  const [, date, time] = match;
  const year = date.substr(0, 4);
  const month = date.substr(4, 2);
  const day = date.substr(6, 2);
  const hour = time.substr(0, 2);
  const minute = time.substr(2, 2);
  const second = time.substr(4, 2);
  
  const dateObj = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`);
  return dateObj.toLocaleString();
}

function showStatus(message, type = 'info') {
  const statusEl = document.getElementById('status');
  statusEl.className = `alert alert-${type}`;
  statusEl.textContent = message;
  statusEl.classList.remove('hidden');
  
  // Auto hide after 5 seconds
  setTimeout(() => {
    statusEl.classList.add('hidden');
  }, 5000);
}

function showError(message) {
  showStatus(message, 'error');
}

function showSuccess(message) {
  showStatus(message, 'success');
}

/**
 * 🎬 Initialize when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
  // Add keyboard shortcuts
  document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey) {
      switch(e.key) {
        case 'h':
          e.preventDefault();
          checkHealth();
          break;
        case 'l':
          e.preventDefault();
          loadLogList();
          break;
        case 'Escape':
          hideAllDisplays();
          break;
      }
    }
  });
  
  // Focus on health target input
  document.getElementById('healthTarget').focus();
  
  console.log('🚀 Trigger Deploy Home - Initialized');
});
