/**
 * Minimal JavaScript for Newsletter Aggregator
 * Only for HTMX enhancements not possible with HTMX alone
 */

// Auto-refresh status indicators after operations complete
document.body.addEventListener('htmx:afterSwap', function(event) {
    // If a collection/processing/consolidation operation completed,
    // refresh the dashboard stats
    if (event.detail.target.id && 
        (event.detail.target.id.includes('status') || 
         event.detail.target.id.includes('collection') ||
         event.detail.target.id.includes('processing') ||
         event.detail.target.id.includes('consolidation'))) {
        
        // Small delay to ensure database is updated
        setTimeout(function() {
            // Trigger a refresh of the page to update stats
            // HTMX will handle this gracefully
            if (window.location.pathname === '/') {
                htmx.ajax('GET', '/', {target: '.dashboard-stats', swap: 'outerHTML'});
            }
        }, 500);
    }
});

// Add loading states to buttons during HTMX requests
document.body.addEventListener('htmx:beforeRequest', function(event) {
    const button = event.detail.elt.querySelector('button[type="submit"]');
    if (button) {
        button.disabled = true;
        button.textContent = button.textContent.replace(/^([^…]+)/, '$1…');
    }
});

document.body.addEventListener('htmx:afterRequest', function(event) {
    const button = event.detail.elt.querySelector('button[type="submit"]');
    if (button && !event.detail.failed) {
        button.disabled = false;
        // Restore original text (remove ellipsis)
        const originalText = button.getAttribute('data-original-text') || button.textContent.replace('…', '');
        button.textContent = originalText;
    }
});

// Store original button text on page load
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('button[type="submit"]').forEach(function(button) {
        if (!button.getAttribute('data-original-text')) {
            button.setAttribute('data-original-text', button.textContent);
        }
    });
});
