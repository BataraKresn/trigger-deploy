// Help Center JavaScript - Modern Interactive Experience
document.addEventListener('DOMContentLoaded', function() {
    console.log('Help Center loaded successfully');
    initializeHelpCenter();
});

function initializeHelpCenter() {
    setupSearchFunctionality();
    setupExpandableCards();
    setupKeyboardNavigation();
    setupAnimations();
}

// Enhanced Search Functionality
function setupSearchFunctionality() {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');

    if (searchInput && searchBtn) {
        // Search on button click
        searchBtn.addEventListener('click', function() {
            const query = searchInput.value.trim();
            if (query) {
                performSearch(query);
            }
        });

        // Search on Enter key
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    performSearch(query);
                }
            }
        });

        // Live search as user types (debounced)
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length > 2) {
                searchTimeout = setTimeout(() => {
                    performSearch(query);
                }, 300);
            } else if (query.length === 0) {
                clearSearch();
            }
        });
    }
}

function performSearch(query) {
    const helpCards = document.querySelectorAll('.help-card');
    const searchTerm = query.toLowerCase();
    let hasResults = false;

    helpCards.forEach(card => {
        const cardText = card.textContent.toLowerCase();
        const isMatch = cardText.includes(searchTerm);
        
        if (isMatch) {
            card.style.display = 'block';
            card.classList.add('search-highlight');
            hasResults = true;
            
            // Auto-expand matching cards
            const content = card.querySelector('.help-content-section');
            const header = card.querySelector('.help-card-header');
            if (content && !content.classList.contains('active')) {
                if (window.toggleHelpSection) {
                    window.toggleHelpSection(header);
                }
            }
            
            // Highlight matching text
            highlightSearchTerms(card, searchTerm);
        } else {
            card.style.display = 'none';
            card.classList.remove('search-highlight');
        }
    });

    if (!hasResults) {
        showNoResultsMessage(query);
    } else {
        hideNoResultsMessage();
    }
}

function clearSearch() {
    const helpCards = document.querySelectorAll('.help-card');
    helpCards.forEach(card => {
        card.style.display = 'block';
        card.classList.remove('search-highlight');
        removeHighlight(card);
    });
    hideNoResultsMessage();
}

function highlightSearchTerms(card, searchTerm) {
    // Simple text highlighting implementation
    const textElements = card.querySelectorAll('p, h4, li');
    textElements.forEach(element => {
        const text = element.innerHTML;
        if (element.textContent.toLowerCase().includes(searchTerm)) {
            const highlightedText = text.replace(
                new RegExp(`(${searchTerm})`, 'gi'),
                '<mark style="background: #fbbf24; padding: 0.1em 0.2em; border-radius: 0.2em;">$1</mark>'
            );
            element.innerHTML = highlightedText;
        }
    });
}

function removeHighlight(card) {
    const marks = card.querySelectorAll('mark');
    marks.forEach(mark => {
        mark.outerHTML = mark.innerHTML;
    });
}

function showNoResultsMessage(query) {
    hideNoResultsMessage();
    
    const helpGrid = document.querySelector('.help-grid');
    if (helpGrid) {
        const noResults = document.createElement('div');
        noResults.id = 'no-results';
        noResults.className = 'no-results-message';
        noResults.innerHTML = `
            <div style="text-align: center; padding: 3rem; background: var(--bg-card); border-radius: var(--border-radius); border: 1px solid var(--border-color);">
                <i class="fas fa-search" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 1rem;"></i>
                <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">No results found</h3>
                <p style="color: var(--text-secondary); margin-bottom: 1rem;">We couldn't find anything matching "${query}"</p>
                <button onclick="clearSearchAndFocus()" 
                        style="padding: 0.75rem 1.5rem; background: var(--primary-color); color: white; border: none; border-radius: 0.5rem; cursor: pointer;">
                    Clear Search
                </button>
            </div>
        `;
        
        helpGrid.appendChild(noResults);
    }
}

function hideNoResultsMessage() {
    const noResults = document.getElementById('no-results');
    if (noResults) {
        noResults.remove();
    }
}

// Enhanced Expandable Cards
function setupExpandableCards() {
    // This function is now handled by the global toggleHelpSection function
    // which is defined in the HTML template for better integration
}

// Keyboard Navigation
function setupKeyboardNavigation() {
    document.addEventListener('keydown', function(e) {
        // ESC to clear search
        if (e.key === 'Escape') {
            const searchInput = document.getElementById('search-input');
            if (searchInput && searchInput.value) {
                searchInput.value = '';
                clearSearch();
                searchInput.blur();
            }
        }
        
        // Arrow keys for card navigation
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            const focusedElement = document.activeElement;
            if (focusedElement.classList.contains('help-card-header')) {
                e.preventDefault();
                const cards = Array.from(document.querySelectorAll('.help-card-header'));
                const currentIndex = cards.indexOf(focusedElement);
                
                let nextIndex;
                if (e.key === 'ArrowDown') {
                    nextIndex = currentIndex + 1 >= cards.length ? 0 : currentIndex + 1;
                } else {
                    nextIndex = currentIndex - 1 < 0 ? cards.length - 1 : currentIndex - 1;
                }
                
                cards[nextIndex].focus();
            }
        }
        
        // Enter or Space to toggle card
        if ((e.key === 'Enter' || e.key === ' ') && e.target.classList.contains('help-card-header')) {
            e.preventDefault();
            if (window.toggleHelpSection) {
                window.toggleHelpSection(e.target);
            }
        }
    });
    
    // Make card headers focusable
    const cardHeaders = document.querySelectorAll('.help-card-header');
    cardHeaders.forEach(header => {
        header.setAttribute('tabindex', '0');
        header.setAttribute('role', 'button');
        header.setAttribute('aria-expanded', 'false');
    });
}

// Smooth Animations
function setupAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe all help cards
    const helpCards = document.querySelectorAll('.help-card');
    helpCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(card);
    });
    
    // Add CSS for animation
    const style = document.createElement('style');
    style.textContent = `
        .help-card.animate-in {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
        
        .help-card-header:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }
        
        .search-highlight {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
        }
    `;
    document.head.appendChild(style);
}

// Global helper functions
window.clearSearchAndFocus = function() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.value = '';
        clearSearch();
        searchInput.focus();
    }
}

// Global function for toggling help sections (called from HTML)
window.toggleHelpSection = function(header) {
    const card = header.parentElement;
    const content = card.querySelector('.help-content-section');
    const icon = header.querySelector('.expand-icon');
    
    if (content.classList.contains('active')) {
        content.classList.remove('active');
        card.classList.remove('expanded');
        icon.textContent = '⌄';
        header.setAttribute('aria-expanded', 'false');
    } else {
        content.classList.add('active');
        card.classList.add('expanded');
        icon.textContent = '⌃';
        header.setAttribute('aria-expanded', 'true');
    }
}

// Auto-expand first card on load
window.addEventListener('load', function() {
    const firstCard = document.querySelector('.help-card .help-card-header');
    if (firstCard) {
        setTimeout(() => {
            if (window.toggleHelpSection) {
                window.toggleHelpSection(firstCard);
            }
        }, 500);
    }
});
