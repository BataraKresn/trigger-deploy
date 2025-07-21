/**
 * User Management JavaScript
 * Handles CRUD operations, modals, and user interactions
 */

class UserManager {
    constructor() {
        this.users = [];
        this.currentEditUser = null;
        this.searchTerm = '';
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadUsers();
    }

    bindEvents() {
        // Search functionality
        document.getElementById('userSearch')?.addEventListener('input', (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            this.renderUsers();
        });

        // Create user button
        document.getElementById('createUserBtn')?.addEventListener('click', () => {
            this.openCreateModal();
        });

        // Form submissions
        document.getElementById('userForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleUserSubmit();
        });

        document.getElementById('passwordForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handlePasswordSubmit();
        });

        // Modal close events
        document.querySelectorAll('[data-modal-close]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modalId = e.target.getAttribute('data-modal-close');
                this.closeModal(modalId);
            });
        });

        // Password visibility toggles
        document.querySelectorAll('.password-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                const input = e.target.previousElementSibling;
                const icon = e.target;
                
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.textContent = '👁️';
                } else {
                    input.type = 'password';
                    icon.textContent = '👁️‍🗨️';
                }
            });
        });

        // Modal backdrop clicks
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }

    async loadUsers() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/users', {
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load users');
            }

            const data = await response.json();
            this.users = data.users || [];
            this.renderUsers();
            this.updateStats();
        } catch (error) {
            console.error('Error loading users:', error);
            this.showError('Failed to load users. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    renderUsers() {
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;

        const filteredUsers = this.users.filter(user => {
            if (!this.searchTerm) return true;
            
            return (
                user.nama_lengkap.toLowerCase().includes(this.searchTerm) ||
                user.username.toLowerCase().includes(this.searchTerm) ||
                user.email.toLowerCase().includes(this.searchTerm) ||
                user.role.toLowerCase().includes(this.searchTerm)
            );
        });

        if (filteredUsers.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-state">
                        <h3>No users found</h3>
                        <p>${this.searchTerm ? 'Try adjusting your search criteria' : 'No users available'}</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = filteredUsers.map(user => this.renderUserRow(user)).join('');
    }

    renderUserRow(user) {
        const initials = this.getInitials(user.nama_lengkap);
        const isCurrentUser = user.username === this.getCurrentUsername();
        
        return `
            <tr data-user-id="${user.id}" class="user-row">
                <td>
                    <div class="user-info-cell">
                        <div class="user-avatar">${initials}</div>
                        <div class="user-details">
                            <div class="user-name">${this.escapeHtml(user.nama_lengkap)}</div>
                            <div class="user-username">@${this.escapeHtml(user.username)}</div>
                        </div>
                    </div>
                </td>
                <td>${this.escapeHtml(user.email)}</td>
                <td>
                    <span class="role-badge ${user.role}">
                        ${user.role === 'superadmin' ? '👑' : '👤'} ${user.role}
                    </span>
                </td>
                <td>
                    <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                        ${user.is_active ? '✅ Active' : '❌ Inactive'}
                    </span>
                </td>
                <td>${new Date(user.created_at).toLocaleDateString()}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn edit" onclick="userManager.editUser('${user.id}')" 
                                ${isCurrentUser ? '' : ''}>
                            ✏️ Edit
                        </button>
                        <button class="action-btn password" onclick="userManager.changePassword('${user.id}')">
                            🔑 Password
                        </button>
                        <button class="action-btn delete" onclick="userManager.deleteUser('${user.id}')" 
                                ${isCurrentUser ? 'disabled title="Cannot delete yourself"' : ''}>
                            🗑️ Delete
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    updateStats() {
        const totalUsers = this.users.length;
        const activeUsers = this.users.filter(u => u.is_active).length;
        const superadmins = this.users.filter(u => u.role === 'superadmin').length;

        // Update stats in the header or stats section if they exist
        const statsElements = {
            'totalUsers': totalUsers,
            'activeUsers': activeUsers,
            'superadmins': superadmins,
            'regularUsers': totalUsers - superadmins
        };

        Object.entries(statsElements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }

    openCreateModal() {
        this.currentEditUser = null;
        document.getElementById('modalTitle').textContent = 'Create New User';
        document.getElementById('userForm').reset();
        document.getElementById('confirmPassword').closest('.form-group').style.display = 'block';
        this.openModal('userModal');
    }

    editUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        this.currentEditUser = user;
        document.getElementById('modalTitle').textContent = 'Edit User';
        
        // Fill form with user data
        document.getElementById('namaLengkap').value = user.nama_lengkap;
        document.getElementById('username').value = user.username;
        document.getElementById('email').value = user.email;
        document.getElementById('role').value = user.role;
        document.getElementById('isActive').checked = user.is_active;
        
        // Hide confirm password for edit
        document.getElementById('confirmPassword').closest('.form-group').style.display = 'none';
        document.getElementById('password').required = false;
        
        this.openModal('userModal');
    }

    changePassword(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        this.currentEditUser = user;
        document.getElementById('passwordModalTitle').textContent = `Change Password - ${user.nama_lengkap}`;
        document.getElementById('passwordForm').reset();
        this.openModal('passwordModal');
    }

    async deleteUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        // Setup delete modal
        document.getElementById('deleteUserName').textContent = user.nama_lengkap;
        document.getElementById('deleteUsername').textContent = user.username;
        
        this.currentEditUser = user;
        this.openModal('deleteModal');
    }

    async confirmDelete() {
        if (!this.currentEditUser) return;

        try {
            const response = await fetch(`/api/users/${this.currentEditUser.id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete user');
            }

            this.showSuccess('User deleted successfully');
            this.closeModal('deleteModal');
            this.loadUsers();
        } catch (error) {
            console.error('Error deleting user:', error);
            this.showError('Failed to delete user. Please try again.');
        }
    }

    async handleUserSubmit() {
        const formData = new FormData(document.getElementById('userForm'));
        const userData = Object.fromEntries(formData.entries());
        
        // Convert checkbox to boolean
        userData.is_active = formData.has('is_active');

        // Validation
        if (!this.validateUserForm(userData)) return;

        try {
            const url = this.currentEditUser 
                ? `/api/users/${this.currentEditUser.id}`
                : '/api/users';
            
            const method = this.currentEditUser ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to save user');
            }

            const message = this.currentEditUser ? 'User updated successfully' : 'User created successfully';
            this.showSuccess(message);
            this.closeModal('userModal');
            this.loadUsers();
        } catch (error) {
            console.error('Error saving user:', error);
            this.showError(error.message || 'Failed to save user. Please try again.');
        }
    }

    async handlePasswordSubmit() {
        const formData = new FormData(document.getElementById('passwordForm'));
        const newPassword = formData.get('newPassword');
        const confirmPassword = formData.get('confirmPassword');

        if (newPassword !== confirmPassword) {
            this.showError('Passwords do not match');
            return;
        }

        if (newPassword.length < 6) {
            this.showError('Password must be at least 6 characters long');
            return;
        }

        try {
            const response = await fetch(`/api/users/${this.currentEditUser.id}/password`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getToken()}`
                },
                body: JSON.stringify({ password: newPassword })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to change password');
            }

            this.showSuccess('Password changed successfully');
            this.closeModal('passwordModal');
        } catch (error) {
            console.error('Error changing password:', error);
            this.showError(error.message || 'Failed to change password. Please try again.');
        }
    }

    validateUserForm(userData) {
        if (!userData.nama_lengkap || !userData.username || !userData.email) {
            this.showError('Please fill in all required fields');
            return false;
        }

        if (!this.isValidEmail(userData.email)) {
            this.showError('Please enter a valid email address');
            return false;
        }

        if (!this.currentEditUser && (!userData.password || userData.password.length < 6)) {
            this.showError('Password must be at least 6 characters long');
            return false;
        }

        if (!this.currentEditUser && userData.password !== userData.confirmPassword) {
            this.showError('Passwords do not match');
            return false;
        }

        return true;
    }

    // Utility methods
    openModal(modalId) {
        document.getElementById(modalId).style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
        document.body.style.overflow = 'auto';
        this.currentEditUser = null;
    }

    showLoading(show) {
        const container = document.getElementById('usersContainer');
        if (container) {
            container.classList.toggle('loading', show);
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    getToken() {
        return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    }

    getCurrentUsername() {
        try {
            const token = this.getToken();
            if (!token) return null;
            
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.username;
        } catch {
            return null;
        }
    }

    getInitials(name) {
        return name.split(' ')
            .map(word => word.charAt(0))
            .join('')
            .toUpperCase()
            .substring(0, 2);
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.userManager = new UserManager();
});

// Add notification styles dynamically
const notificationStyles = `
<style>
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    min-width: 300px;
    max-width: 500px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    animation: slideIn 0.3s ease;
}

.notification-success {
    border-left: 4px solid #48bb78;
}

.notification-error {
    border-left: 4px solid #f56565;
}

.notification-info {
    border-left: 4px solid #4299e1;
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
}

.notification-icon {
    font-size: 18px;
}

.notification-message {
    flex: 1;
    font-weight: 500;
}

.notification-close {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: #a0aec0;
    padding: 0;
    width: 20px;
    height: 20px;
}

.notification-close:hover {
    color: #718096;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', notificationStyles);
