// Basic JavaScript for Spades Score Keeper

// Utility functions
function showFlash(message, type = 'info') {
    const flash = document.createElement('div');
    flash.className = `flash ${type}`;
    flash.textContent = message;
    
    const content = document.querySelector('.content');
    content.insertBefore(flash, content.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        flash.remove();
    }, 5000);
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const required = form.querySelectorAll('[required]');
    let valid = true;
    
    required.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('error');
            valid = false;
        } else {
            field.classList.remove('error');
        }
    });
    
    return valid;
}

// Auto-focus first input
document.addEventListener('DOMContentLoaded', function() {
    const firstInput = document.querySelector('input:not([type="hidden"])');
    if (firstInput) {
        firstInput.focus();
    }
});

// Handle Enter key for form submission
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
        const form = e.target.closest('form');
        if (form) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.click();
            }
        }
    }
});

// Mobile touch improvements
document.addEventListener('touchstart', function() {}, {passive: true});

// Add loading state to buttons
function addLoadingState(button) {
    button.disabled = true;
    button.textContent = 'Loading...';
}

// Remove loading state from buttons
function removeLoadingState(button, originalText) {
    button.disabled = false;
    button.textContent = originalText;
}

// Handle form submissions with loading states
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.textContent;
                addLoadingState(submitBtn);
                
                // Restore button state if submission fails
                setTimeout(() => {
                    removeLoadingState(submitBtn, originalText);
                }, 3000);
            }
        });
    });
});

// PWA-like behavior for mobile
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Future: Add service worker for offline functionality
    });
}

// Prevent zoom on double-tap for iOS
let lastTouchEnd = 0;
document.addEventListener('touchend', function(event) {
    const now = (new Date()).getTime();
    if (now - lastTouchEnd <= 300) {
        event.preventDefault();
    }
    lastTouchEnd = now;
}, false);