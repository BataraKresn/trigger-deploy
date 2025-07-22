// Help Center JavaScript - Optimized for fast loading
document.addEventListener('DOMContentLoaded', function() {
    console.log('Help Center loaded successfully');

    // Search functionality
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');

    if (searchInput && searchBtn) {
        searchBtn.addEventListener('click', function() {
            const query = searchInput.value.trim();
            if (query) {
                searchHelp(query);
            }
        });

        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    searchHelp(query);
                }
            }
        });
    }

    // Expandable sections
    const helpCards = document.querySelectorAll('.help-card');
    helpCards.forEach(card => {
        const header = card.querySelector('.help-card-header');
        if (header) {
            header.addEventListener('click', function() {
                const content = card.querySelector('.help-content-section');
                const expandIcon = header.querySelector('.expand-icon');
                
                if (content && expandIcon) {
                    if (content.style.display === 'none' || !content.style.display) {
                        content.style.display = 'block';
                        expandIcon.textContent = '▲';
                    } else {
                        content.style.display = 'none';
                        expandIcon.textContent = '▼';
                    }
                }
            });
        }
    });

    // FAQ items
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        if (question) {
            question.addEventListener('click', function() {
                const answer = item.querySelector('.faq-answer');
                if (answer) {
                    answer.style.display = answer.style.display === 'none' ? 'block' : 'none';
                }
            });
        }
    });

    // Form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            showSuccessMessage('Thank you! Your request has been submitted.');
        });
    });
});

function searchHelp(query) {
    // Simple search functionality
    const sections = document.querySelectorAll('.help-content-section, .faq-item');
    const normalizedQuery = query.toLowerCase();
    
    sections.forEach(section => {
        const text = section.textContent.toLowerCase();
        if (text.includes(normalizedQuery)) {
            section.style.display = 'block';
            section.style.backgroundColor = '#fffbf0';
            section.style.border = '2px solid #f59e0b';
        } else {
            section.style.display = 'none';
        }
    });

    // Show message if no results
    const visibleSections = document.querySelectorAll('.help-content-section[style*="block"], .faq-item[style*="block"]');
    if (visibleSections.length === 0) {
        showMessage('No results found for "' + query + '". Try different keywords.', 'warning');
    }
}

function showMessage(message, type = 'info') {
    // Create and show message
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    switch(type) {
        case 'success':
            messageDiv.style.backgroundColor = '#10b981';
            break;
        case 'warning':
            messageDiv.style.backgroundColor = '#f59e0b';
            break;
        case 'error':
            messageDiv.style.backgroundColor = '#ef4444';
            break;
        default:
            messageDiv.style.backgroundColor = '#3b82f6';
    }
    
    messageDiv.textContent = message;
    document.body.appendChild(messageDiv);
    
    // Animate in
    setTimeout(() => messageDiv.style.opacity = '1', 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        setTimeout(() => messageDiv.remove(), 300);
    }, 3000);
}

function showSuccessMessage(message) {
    showMessage(message, 'success');
}
