// Help Center JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize Help Center functionality
    initHelpCenter();
    
    function initHelpCenter() {
        setupSearchFunctionality();
        setupCardToggling();
        setupFeatureRequestForm();
        setupContactMethods();
        setupScrollToTop();
    }
    
    // Search functionality
    function setupSearchFunctionality() {
        const searchInput = document.getElementById('search-input');
        const searchBtn = document.getElementById('search-btn');
        const helpCards = document.querySelectorAll('.help-card');
        
        function performSearch() {
            const query = searchInput.value.toLowerCase().trim();
            
            if (query === '') {
                showAllCards();
                return;
            }
            
            let foundResults = false;
            
            helpCards.forEach(card => {
                const cardContent = card.textContent.toLowerCase();
                const isMatch = cardContent.includes(query);
                
                if (isMatch) {
                    card.style.display = 'block';
                    foundResults = true;
                    
                    // Auto-expand matching cards
                    if (!card.classList.contains('active')) {
                        toggleCard(card);
                    }
                    
                    // Highlight matching text
                    highlightSearchTerms(card, query);
                } else {
                    card.style.display = 'none';
                }
            });
            
            if (!foundResults) {
                showNoResultsMessage();
            }
        }
        
        function showAllCards() {
            helpCards.forEach(card => {
                card.style.display = 'block';
                removeHighlights(card);
            });
            hideNoResultsMessage();
        }
        
        function highlightSearchTerms(card, query) {
            const contentSection = card.querySelector('.help-content-section');
            if (!contentSection) return;
            
            const walker = document.createTreeWalker(
                contentSection,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            const textNodes = [];
            let node;
            
            while (node = walker.nextNode()) {
                textNodes.push(node);
            }
            
            textNodes.forEach(textNode => {
                const text = textNode.textContent;
                const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
                
                if (regex.test(text)) {
                    const highlightedText = text.replace(regex, '<mark>$1</mark>');
                    const span = document.createElement('span');
                    span.innerHTML = highlightedText;
                    textNode.parentNode.replaceChild(span, textNode);
                }
            });
        }
        
        function removeHighlights(card) {
            const marks = card.querySelectorAll('mark');
            marks.forEach(mark => {
                const parent = mark.parentNode;
                parent.replaceChild(document.createTextNode(mark.textContent), mark);
                parent.normalize();
            });
        }
        
        function showNoResultsMessage() {
            hideNoResultsMessage();
            
            const noResults = document.createElement('div');
            noResults.id = 'no-results-message';
            noResults.className = 'no-results-message';
            noResults.innerHTML = `
                <div style="text-align: center; padding: 3rem; color: #64748b;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                    <h3>No results found</h3>
                    <p>Try different search terms or browse the categories below.</p>
                </div>
            `;
            
            const helpGrid = document.querySelector('.help-grid');
            helpGrid.parentNode.insertBefore(noResults, helpGrid);
        }
        
        function hideNoResultsMessage() {
            const existing = document.getElementById('no-results-message');
            if (existing) {
                existing.remove();
            }
        }
        
        function escapeRegex(string) {
            return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }
        
        // Event listeners
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        searchInput.addEventListener('input', function() {
            if (searchInput.value.trim() === '') {
                showAllCards();
            }
        });
    }
    
    // Card toggling functionality
    function setupCardToggling() {
        const helpCards = document.querySelectorAll('.help-card');
        
        helpCards.forEach(card => {
            const header = card.querySelector('.help-card-header');
            header.addEventListener('click', () => toggleCard(card));
        });
    }
    
    function toggleCard(card) {
        const contentSection = card.querySelector('.help-content-section');
        const expandIcon = card.querySelector('.expand-icon');
        
        card.classList.toggle('active');
        contentSection.classList.toggle('active');
        
        // Smooth animation
        if (contentSection.classList.contains('active')) {
            contentSection.style.maxHeight = contentSection.scrollHeight + 'px';
        } else {
            contentSection.style.maxHeight = '0';
        }
    }
    
    // Feature Request Form functionality
    function setupFeatureRequestForm() {
        const form = document.getElementById('feature-request-form');
        if (!form) return;
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = {
                title: formData.get('feature-title'),
                description: formData.get('feature-description'),
                priority: formData.get('feature-priority'),
                category: formData.get('feature-category')
            };
            
            // Validate form
            if (!data.title || !data.description) {
                showNotification('Please fill in all required fields.', 'error');
                return;
            }
            
            // Submit feature request
            submitFeatureRequest(data);
        });
    }
    
    function submitFeatureRequest(data) {
        // Show loading state
        const submitBtn = document.querySelector('#feature-request-form button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Submitting...';
        submitBtn.disabled = true;
        
        // Simulate API call (replace with actual endpoint)
        setTimeout(() => {
            showNotification('Feature request submitted successfully! We\'ll review it and get back to you.', 'success');
            
            // Reset form
            document.getElementById('feature-request-form').reset();
            
            // Reset button
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            
            // Add to popular requests (simulate)
            addToPopularRequests(data);
            
        }, 1500);
    }
    
    function addToPopularRequests(data) {
        const popularList = document.querySelector('.popular-requests .request-item');
        if (!popularList) return;
        
        const newRequest = document.createElement('div');
        newRequest.className = 'request-item';
        newRequest.innerHTML = `
            <div class="request-votes">1</div>
            <div class="request-content">
                <h5>${data.title}</h5>
                <p>${data.description.substring(0, 100)}...</p>
                <span class="request-status reviewing">Reviewing</span>
            </div>
        `;
        
        popularList.parentNode.insertBefore(newRequest, popularList);
    }
    
    // Contact Methods functionality
    function setupContactMethods() {
        const contactMethods = document.querySelectorAll('.contact-method');
        
        contactMethods.forEach(method => {
            const button = method.querySelector('button');
            if (!button) return;
            
            button.addEventListener('click', function() {
                const methodType = this.dataset.method;
                handleContactMethod(methodType);
            });
        });
    }
    
    function handleContactMethod(method) {
        switch (method) {
            case 'email':
                window.location.href = 'mailto:support@triggerapp.com?subject=Help Request';
                break;
            case 'chat':
                showChatWidget();
                break;
            case 'ticket':
                showTicketForm();
                break;
            default:
                showNotification('Contact method not available yet.', 'info');
        }
    }
    
    function showChatWidget() {
        // Simulate chat widget
        showNotification('Chat support is currently offline. Please try email or submit a ticket.', 'info');
    }
    
    function showTicketForm() {
        // Create modal for ticket form
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Submit Support Ticket</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <form class="ticket-form">
                    <div class="form-group">
                        <label for="ticket-subject">Subject*</label>
                        <input type="text" id="ticket-subject" name="subject" required>
                    </div>
                    <div class="form-group">
                        <label for="ticket-priority">Priority</label>
                        <select id="ticket-priority" name="priority">
                            <option value="low">Low</option>
                            <option value="medium" selected>Medium</option>
                            <option value="high">High</option>
                            <option value="urgent">Urgent</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="ticket-description">Description*</label>
                        <textarea id="ticket-description" name="description" rows="5" required></textarea>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary modal-close">Cancel</button>
                        <button type="submit" class="btn btn-primary">Submit Ticket</button>
                    </div>
                </form>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Handle modal close
        const closeButtons = modal.querySelectorAll('.modal-close');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => modal.remove());
        });
        
        // Handle form submission
        const form = modal.querySelector('.ticket-form');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const ticketData = {
                subject: formData.get('subject'),
                priority: formData.get('priority'),
                description: formData.get('description')
            };
            
            showNotification('Support ticket submitted successfully! Ticket #' + Math.floor(Math.random() * 10000), 'success');
            modal.remove();
        });
        
        // Focus first input
        setTimeout(() => {
            modal.querySelector('input').focus();
        }, 100);
    }
    
    // Scroll to top functionality
    function setupScrollToTop() {
        const scrollButton = document.createElement('button');
        scrollButton.className = 'scroll-to-top';
        scrollButton.innerHTML = '↑';
        scrollButton.title = 'Scroll to top';
        document.body.appendChild(scrollButton);
        
        scrollButton.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        
        // Show/hide scroll button
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                scrollButton.classList.add('visible');
            } else {
                scrollButton.classList.remove('visible');
            }
        });
    }
    
    // Notification system
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${getNotificationIcon(type)}</span>
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
    }
    
    function getNotificationIcon(type) {
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    }
    
    // Utility functions
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Analytics tracking (optional)
    function trackHelpCenterEvent(action, category = 'Help Center') {
        if (typeof gtag !== 'undefined') {
            gtag('event', action, {
                event_category: category,
                event_label: window.location.pathname
            });
        }
    }
    
    // Track page view
    trackHelpCenterEvent('page_view');
});

// Additional CSS for modal and notifications (injected via JavaScript)
const additionalStyles = `
<style>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    border-radius: 0.5rem;
    padding: 2rem;
    max-width: 500px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e2e8f0;
}

.modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    color: #64748b;
}

.form-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    margin-top: 1.5rem;
}

.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1001;
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    transform: translateX(100%);
    transition: transform 0.3s ease;
    max-width: 400px;
}

.notification.show {
    transform: translateX(0);
}

.notification-content {
    display: flex;
    align-items: center;
    padding: 1rem;
    gap: 0.75rem;
}

.notification-icon {
    font-size: 1.25rem;
    font-weight: bold;
}

.notification-message {
    flex: 1;
}

.notification-close {
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
    color: #64748b;
}

.notification-success {
    border-left: 4px solid #10b981;
}

.notification-success .notification-icon {
    color: #10b981;
}

.notification-error {
    border-left: 4px solid #ef4444;
}

.notification-error .notification-icon {
    color: #ef4444;
}

.notification-warning {
    border-left: 4px solid #f59e0b;
}

.notification-warning .notification-icon {
    color: #f59e0b;
}

.notification-info {
    border-left: 4px solid #06b6d4;
}

.notification-info .notification-icon {
    color: #06b6d4;
}

.scroll-to-top {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 50%;
    width: 3rem;
    height: 3rem;
    font-size: 1.25rem;
    cursor: pointer;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    transform: translateY(100px);
    opacity: 0;
    transition: all 0.3s ease;
    z-index: 999;
}

.scroll-to-top.visible {
    transform: translateY(0);
    opacity: 1;
}

.scroll-to-top:hover {
    background: #1d4ed8;
    transform: translateY(-2px);
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', additionalStyles);
