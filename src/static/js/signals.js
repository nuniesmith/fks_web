/**
 * Real-time signal updates and interactions
 * Phase 2.3: Dashboard Implementation
 */

(function() {
    'use strict';

    // Auto-refresh signals every 30 seconds
    const REFRESH_INTERVAL = 30000;
    let refreshTimer = null;

    function initSignalUpdates() {
        // Only auto-refresh if on signals page
        if (window.location.pathname.includes('/signals')) {
            startAutoRefresh();
        }
    }

    function startAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
        
        refreshTimer = setInterval(() => {
            refreshSignals();
        }, REFRESH_INTERVAL);
    }

    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    }

    function refreshSignals() {
        // Get current filter parameters
        const urlParams = new URLSearchParams(window.location.search);
        const category = urlParams.get('category') || 'swing';
        const useAi = urlParams.get('use_ai') || 'true';
        
        // Reload page with current filters
        window.location.reload();
    }

    // Handle approval/rejection with confirmation
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.action && (form.action.includes('approve') || form.action.includes('reject'))) {
            const action = form.action.includes('approve') ? 'approve' : 'reject';
            const confirmed = confirm(
                action === 'approve' 
                    ? 'Are you sure you want to approve and execute this signal?'
                    : 'Are you sure you want to reject this signal?'
            );
            
            if (!confirmed) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            const button = form.querySelector('button[type="submit"]');
            if (button) {
                button.disabled = true;
                button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Processing...';
            }
        }
    });

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSignalUpdates);
    } else {
        initSignalUpdates();
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', stopAutoRefresh);
})();

