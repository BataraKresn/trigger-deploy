// Contact Page JavaScript - Enhanced User Experience
document.addEventListener('DOMContentLoaded', function() {
    console.log('Contact page loaded successfully');
    initializeContactPage();
});

function initializeContactPage() {
    setupFormValidation();
    setupFormSubmission();
    setupAnimations();
    setupInteractiveElements();
}

// Enhanced Form Validation
function setupFormValidation() {
    const form = document.getElementById('contactForm');
    if (!form) return;

    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    inputs.forEach(input => {
        input.addEventListener('blur', validateField);
        input.addEventListener('input', clearValidationError);
        input.addEventListener('focus', handleFieldFocus);
    });

    // Real-time email validation
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('input', validateEmailReal);
    }

    // Character counter for message
    const messageTextarea = document.getElementById('messageText');
    if (messageTextarea) {
        setupCharacterCounter(messageTextarea);
    }
}

function validateField(e) {
    const field = e.target;
    const value = field.value.trim();
    
    // Remove any existing validation UI
    clearValidationError(e);
    
    if (!value && field.required) {
        showFieldError(field, 'This field is required');
        return false;
    }
    
    if (field.type === 'email' && value && !isValidEmail(value)) {
        showFieldError(field, 'Please enter a valid email address');
        return false;
    }
    
    if (field.name === 'firstName' || field.name === 'lastName') {
        if (value && value.length < 2) {
            showFieldError(field, 'Name must be at least 2 characters long');
            return false;
        }
    }
    
    if (field.name === 'message' && value && value.length < 10) {
        showFieldError(field, 'Message must be at least 10 characters long');
        return false;
    }
    
    // If validation passes
    showFieldSuccess(field);
    return true;
}

function clearValidationError(e) {
    const field = e.target;
    field.style.borderColor = 'var(--border-color)';
    
    // Remove error message
    const errorMsg = field.parentNode.querySelector('.error-message');
    if (errorMsg) {
        errorMsg.remove();
    }
    
    // Remove success/error classes
    field.classList.remove('field-error', 'field-success');
}

function handleFieldFocus(e) {
    const field = e.target;
    field.style.borderColor = 'var(--primary-color)';
    field.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
}

function showFieldError(field, message) {
    field.style.borderColor = 'var(--error-color)';
    field.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.1)';
    field.classList.add('field-error');
    
    // Add error message
    const errorMsg = document.createElement('div');
    errorMsg.className = 'error-message';
    errorMsg.style.cssText = `
        color: var(--error-color);
        font-size: 0.875rem;
        margin-top: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    `;
    errorMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    field.parentNode.appendChild(errorMsg);
}

function showFieldSuccess(field) {
    field.style.borderColor = 'var(--success-color)';
    field.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.1)';
    field.classList.add('field-success');
}

function validateEmailReal(e) {
    const email = e.target.value.trim();
    const field = e.target;
    
    if (email && !isValidEmail(email)) {
        field.style.borderColor = '#f59e0b';
    } else if (email) {
        field.style.borderColor = 'var(--success-color)';
    } else {
        field.style.borderColor = 'var(--border-color)';
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function setupCharacterCounter(textarea) {
    const maxLength = 500;
    const counter = document.createElement('div');
    counter.className = 'character-counter';
    counter.style.cssText = `
        text-align: right;
        font-size: 0.875rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
    `;
    
    textarea.parentNode.appendChild(counter);
    
    function updateCounter() {
        const remaining = maxLength - textarea.value.length;
        counter.textContent = `${textarea.value.length}/${maxLength} characters`;
        
        if (remaining < 50) {
            counter.style.color = 'var(--warning-color)';
        } else if (remaining < 20) {
            counter.style.color = 'var(--error-color)';
        } else {
            counter.style.color = 'var(--text-muted)';
        }
    }
    
    textarea.addEventListener('input', updateCounter);
    updateCounter();
}

// Enhanced Form Submission
function setupFormSubmission() {
    const form = document.getElementById('contactForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validate all fields
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            const fieldValid = validateField({ target: input });
            if (!fieldValid) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            showMessage('Please fix the errors above before submitting.', 'error');
            // Focus on first error field
            const firstError = form.querySelector('.field-error');
            if (firstError) {
                firstError.focus();
            }
            return;
        }
        
        // If validation passes, submit the form
        submitForm(form);
    });
}

function submitForm(form) {
    const formData = new FormData(form);
    const messageDiv = document.getElementById('message');
    const submitBtn = form.querySelector('.submit-btn');
    
    // Show loading state
    const originalBtnContent = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    submitBtn.disabled = true;
    
    // Prepare data for submission
    const data = {
        firstName: formData.get('firstName'),
        lastName: formData.get('lastName'),
        email: formData.get('email'),
        company: formData.get('company'),
        subject: formData.get('subject'),
        message: formData.get('message')
    };
    
    // Send to backend
    fetch('/contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showMessage(result.message, 'success');
            
            // Reset form
            form.reset();
            
            // Clear all validation states
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                clearValidationError({ target: input });
            });
            
            // Reset character counter
            const counter = form.querySelector('.character-counter');
            if (counter) {
                counter.textContent = '0/500 characters';
                counter.style.color = 'var(--text-muted)';
            }
            
            // Show success animation
            showSuccessAnimation();
            
            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
            
        } else {
            showMessage(result.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Sorry, there was an error sending your message. Please try again.', 'error');
    })
    .finally(() => {
        // Reset button
        submitBtn.innerHTML = originalBtnContent;
        submitBtn.disabled = false;
    });
}

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    if (!messageDiv) return;
    
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        ${text}
    `;
    messageDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
}

function showSuccessAnimation() {
    // Create a temporary success animation
    const animation = document.createElement('div');
    animation.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: var(--success-color);
        color: white;
        padding: 2rem;
        border-radius: 50%;
        font-size: 2rem;
        z-index: 1000;
        animation: successPulse 1s ease-out;
    `;
    animation.innerHTML = '<i class="fas fa-check"></i>';
    
    // Add animation keyframes
    const style = document.createElement('style');
    style.textContent = `
        @keyframes successPulse {
            0% { transform: translate(-50%, -50%) scale(0); opacity: 0; }
            50% { transform: translate(-50%, -50%) scale(1.2); opacity: 1; }
            100% { transform: translate(-50%, -50%) scale(1); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(animation);
    
    setTimeout(() => {
        animation.remove();
        style.remove();
    }, 1000);
}

// Interactive Animations
function setupAnimations() {
    // Intersection Observer for contact methods
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 100);
            }
        });
    }, observerOptions);

    // Animate contact methods
    const contactMethods = document.querySelectorAll('.contact-method');
    contactMethods.forEach(method => {
        method.style.opacity = '0';
        method.style.transform = 'translateY(20px)';
        method.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(method);
    });
    
    // Animate form elements
    const formGroups = document.querySelectorAll('.form-group');
    formGroups.forEach((group, index) => {
        group.style.opacity = '0';
        group.style.transform = 'translateX(-20px)';
        group.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(group);
    });
}

function setupInteractiveElements() {
    // Add hover effects to contact methods
    const contactMethods = document.querySelectorAll('.contact-method');
    contactMethods.forEach(method => {
        method.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.02)';
        });
        
        method.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Add ripple effect to submit button
    const submitBtn = document.querySelector('.submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', createRippleEffect);
    }
}

function createRippleEffect(e) {
    const button = e.currentTarget;
    const rect = button.getBoundingClientRect();
    const ripple = document.createElement('span');
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s linear;
    `;
    
    // Add ripple animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    button.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
        style.remove();
    }, 600);
}

// Export functions for global access
window.contactFormUtils = {
    showMessage,
    validateField,
    clearValidationError
};
