// =================================
// Login Page JavaScript
// =================================

// Global variables
let isPasswordVisible = false;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Login page loaded');
    
    // Check if already logged in
    checkExistingSession();
    
    // Setup event listeners
    setupEventListeners();
    
    // Check system status
    checkSystemStatus();
    
    // Load demo info
    loadDemoInfo();
    
    // Load saved credentials if remember me was checked
    loadSavedCredentials();
});

function setupEventListeners() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Enter key handlers
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const activeElement = document.activeElement;
            
            // Handle Enter key on main form only
            if (activeElement.closest('#loginForm')) {
                e.preventDefault();
                handleLogin(e);
            }
        }
        
        // ESC to close modals
        if (e.key === 'Escape') {
            closeForgotPassword();
        }
    });
    
    // Auto-focus on username field
    const usernameField = document.getElementById('username');
    if (usernameField) {
        setTimeout(() => usernameField.focus(), 500);
    }
}

function checkExistingSession() {
    // Check if user has valid session
    const token = localStorage.getItem('authToken');
    const rememberMe = localStorage.getItem('rememberMe');
    
    if (token && rememberMe === 'true') {
        // Verify token with server
        verifyToken(token);
    }
}

function verifyToken(token) {
    showSpinner();
    
    fetch('/api/auth/verify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        
        if (data.valid) {
            // Token is valid, redirect to dashboard
            showStatus('✅ Session restored', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
        } else {
            // Token invalid, clear storage
            clearSession();
        }
    })
    .catch(error => {
        hideSpinner();
        console.error('Token verification error:', error);
        clearSession();
    });
}

function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;
    
    // Validation
    if (!username) {
        showStatus('❌ Please enter username', 'error');
        document.getElementById('username').focus();
        return;
    }
    
    if (!password) {
        showStatus('❌ Please enter password', 'error');
        document.getElementById('password').focus();
        return;
    }
    
    performLogin(username, password, rememberMe);
}

function performLogin(username, password, rememberMe = false) {
    const loginBtn = document.getElementById('loginBtn');
    
    // Update button state
    if (loginBtn) {
        loginBtn.textContent = '🔄 Signing In...';
        loginBtn.disabled = true;
    }
    
    showSpinner();
    showStatus('🔐 Authenticating...', 'info');
    
    // Simulate API call (replace with actual authentication)
    const loginData = {
        username: username,
        password: password,
        remember_me: rememberMe
    };
    
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(loginData)
    })
    .then(response => {
        return response.json().then(data => {
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            return data;
        });
    })
    .then(data => {
        hideSpinner();
        
        if (data.success) {
            // Login successful
            const welcomeMessage = data.message || '✅ Login successful! Redirecting...';
            showStatus(welcomeMessage, 'success');
            
            // Save session data
            if (data.token) {
                localStorage.setItem('authToken', data.token);
                localStorage.setItem('userData', JSON.stringify(data.user));
                
                if (rememberMe) {
                    localStorage.setItem('rememberMe', 'true');
                    // Save credentials (encrypted in real app)
                    localStorage.setItem('savedUsername', username);
                }
            }
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
            
        } else {
            // Login failed
            throw new Error(data.error || 'Login failed');
        }
    })
    .catch(error => {
        hideSpinner();
        
        // More specific error messages
        let errorMessage = error.message;
        if (errorMessage.includes('Invalid password')) {
            errorMessage = '❌ Incorrect password. Please check your LOGIN_PASSWORD.';
        } else if (errorMessage.includes('Username is required')) {
            errorMessage = '❌ Please enter a username.';
        } else if (errorMessage.includes('Password is required')) {
            errorMessage = '❌ Please enter your password.';
        } else if (errorMessage.includes('fetch')) {
            errorMessage = '❌ Connection error. Please check if the server is running.';
        }
        
        showStatus(errorMessage, 'error');
        console.error('Login error:', error);
        
        // Reset button
        if (loginBtn) {
            loginBtn.textContent = '🚀 Sign In';
            loginBtn.disabled = false;
        }
        
        // Focus back to password field for retry
        document.getElementById('password').focus();
        document.getElementById('password').select();
    });
}

function loginWithToken() {
    const token = document.getElementById('deployToken').value.trim();
    
    if (!token) {
        showStatus('❌ Please enter deployment token', 'error');
        document.getElementById('deployToken').focus();
        return;
    }
    
    showSpinner();
    showStatus('⚡ Verifying token...', 'info');
    
    fetch('/api/auth/token-login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token: token })
    })
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        
        if (data.success) {
            showStatus('✅ Token verified! Redirecting...', 'success');
            
            // Save limited session for token-based access
            localStorage.setItem('deployToken', token);
            localStorage.setItem('userName', 'Token User');
            localStorage.setItem('userRole', 'deploy');
            
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
            
        } else {
            throw new Error(data.message || 'Invalid token');
        }
    })
    .catch(error => {
        hideSpinner();
        showStatus(`❌ ${error.message}`, 'error');
        console.error('Token login error:', error);
        
        // Clear token field
        document.getElementById('deployToken').value = '';
        document.getElementById('deployToken').focus();
    });
}

function togglePassword() {
    const passwordField = document.getElementById('password');
    const toggleBtn = document.querySelector('.password-toggle');
    
    if (isPasswordVisible) {
        passwordField.type = 'password';
        toggleBtn.textContent = '👁️';
        isPasswordVisible = false;
    } else {
        passwordField.type = 'text';
        toggleBtn.textContent = '🙈';
        isPasswordVisible = true;
    }
}

function showForgotPassword() {
    const modal = document.getElementById('forgotPasswordModal');
    if (modal) {
        modal.classList.remove('hidden');
        
        // Focus on email field
        setTimeout(() => {
            const emailField = document.getElementById('resetEmail');
            if (emailField) emailField.focus();
        }, 300);
    }
}

function closeForgotPassword() {
    const modal = document.getElementById('forgotPasswordModal');
    if (modal) {
        modal.classList.add('hidden');
        
        // Clear form
        const emailField = document.getElementById('resetEmail');
        if (emailField) emailField.value = '';
    }
}

function requestPasswordReset() {
    const email = document.getElementById('resetEmail').value.trim();
    
    if (!email) {
        showStatus('❌ Please enter email address', 'error');
        return;
    }
    
    if (!isValidEmail(email)) {
        showStatus('❌ Please enter valid email address', 'error');
        return;
    }
    
    showSpinner();
    
    fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        hideSpinner();
        
        if (data.success) {
            showStatus('✅ Reset request sent! Check your email.', 'success');
            closeForgotPassword();
        } else {
            throw new Error(data.message || 'Reset request failed');
        }
    })
    .catch(error => {
        hideSpinner();
        showStatus(`❌ ${error.message}`, 'error');
        console.error('Password reset error:', error);
    });
}

function checkSystemStatus() {
    fetch('/api/health/system')
    .then(response => response.json())
    .then(data => {
        updateSystemStatus(data.status || 'unknown');
    })
    .catch(error => {
        console.error('System status check error:', error);
        updateSystemStatus('error');
    });
}

function updateSystemStatus(status) {
    const statusIndicator = document.getElementById('systemStatus');
    const statusText = document.getElementById('systemStatusText');
    
    if (statusIndicator && statusText) {
        switch(status) {
            case 'healthy':
                statusIndicator.textContent = '🟢';
                statusText.textContent = 'Online';
                break;
            case 'warning':
                statusIndicator.textContent = '🟡';
                statusText.textContent = 'Limited';
                break;
            case 'error':
                statusIndicator.textContent = '🔴';
                statusText.textContent = 'Issues';
                break;
            default:
                statusIndicator.textContent = '🟡';
                statusText.textContent = 'Unknown';
        }
    }
}

// Load demo credentials info from server
function loadDemoInfo() {
    fetch('/api/auth/demo-info')
        .then(response => response.json())
        .then(data => {
            if (data.demo_available) {
                updateDemoCredentials(data);
            } else {
                hideDemoCredentials();
            }
        })
        .catch(error => {
            console.log('Demo info not available:', error);
            // Keep default display
        });
}

function updateDemoCredentials(demoData) {
    const demoInfo = document.querySelector('.demo-info');
    if (!demoInfo) return;
    
    const credentialsDiv = demoInfo.querySelector('.demo-credentials');
    if (credentialsDiv) {
        credentialsDiv.innerHTML = `
            <p><strong>Username:</strong> ${demoData.username_example} (atau username apapun)</p>
            <p><strong>Password:</strong> ${demoData.password_hint}</p>
            <p><strong>Deploy Token:</strong> ${demoData.token_hint}</p>
        `;
    }
    
    const noteElement = demoInfo.querySelector('.demo-note');
    if (noteElement) {
        noteElement.textContent = `🔧 ${demoData.note}`;
    }
}

function hideDemoCredentials() {
    const demoInfo = document.querySelector('.demo-info');
    if (demoInfo) {
        demoInfo.style.display = 'none';
    }
}

function loadSavedCredentials() {
    const rememberMe = localStorage.getItem('rememberMe');
    const savedUsername = localStorage.getItem('savedUsername');
    
    if (rememberMe === 'true' && savedUsername) {
        document.getElementById('username').value = savedUsername;
        document.getElementById('rememberMe').checked = true;
        
        // Focus on password field
        setTimeout(() => {
            document.getElementById('password').focus();
        }, 500);
    }
}

function clearSession() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('deployToken');
    localStorage.removeItem('userName');
    localStorage.removeItem('userRole');
    localStorage.removeItem('rememberMe');
    localStorage.removeItem('savedUsername');
}

// Utility Functions
function showStatus(message, type = 'info') {
    const status = document.getElementById('loginStatus');
    if (!status) return;
    
    status.className = `status-message ${type}`;
    status.textContent = message;
    status.classList.remove('hidden');
    
    // Auto hide non-error messages
    if (type !== 'error') {
        setTimeout(() => hideStatus(), 3000);
    }
}

function hideStatus() {
    const status = document.getElementById('loginStatus');
    if (status) {
        status.classList.add('hidden');
    }
}

function showSpinner() {
    const spinner = document.getElementById('loginSpinner');
    if (spinner) {
        spinner.classList.remove('hidden');
    }
}

function hideSpinner() {
    const spinner = document.getElementById('loginSpinner');
    if (spinner) {
        spinner.classList.add('hidden');
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Demo functions (remove in production)
function demoLogin() {
    document.getElementById('username').value = 'admin';
    document.getElementById('password').value = 'admin123';
    showStatus('💡 Demo credentials loaded', 'info');
}

// Add demo button in development
if (window.location.hostname === 'localhost' || window.location.hostname.includes('dev')) {
    document.addEventListener('DOMContentLoaded', function() {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            const demoBtn = document.createElement('button');
            demoBtn.type = 'button';
            demoBtn.className = 'btn btn-secondary btn-full';
            demoBtn.textContent = '🧪 Demo Login';
            demoBtn.onclick = demoLogin;
            demoBtn.style.marginTop = '0.5rem';
            loginForm.appendChild(demoBtn);
        }
    });
}
