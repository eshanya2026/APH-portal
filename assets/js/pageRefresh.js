/**
 * APH Portal - Intelligent Navigation & Subpage Return Handler
 * Guarantees that "Back to Main Portal" returns to the already-opened
 * portal tab rather than opening duplicate tabs.
 */

window.backToMainPortal = function(e, targetHash) {
    if (e && e.preventDefault) {
        e.preventDefault();
    }

    const cleanHash = targetHash ? (targetHash.startsWith('#') ? targetHash : '#' + targetHash) : '';

    // 1. If opened from an active opener window (e.g. main portal tab is already open)
    if (window.opener && !window.opener.closed) {
        try {
            if (cleanHash && window.opener.location) {
                const base = window.opener.location.href.split('#')[0];
                window.opener.location.replace(base + cleanHash);
            }
            window.opener.focus();
        } catch (err) {}
        
        // Attempt immediate window close
        try {
            window.close();
        } catch (err) {}

        // If closed, return immediately
        if (window.closed) {
            return false;
        }

        // Give the browser 150ms to close or switch focus to opener
        setTimeout(function() {
            try {
                window.opener.focus();
                window.close();
            } catch (err) {}

            // DO NOT navigate this tab to index.html if opener is alive — that would create a duplicate tab!
            // Instead, if the browser blocked window.close(), politely close history or show return notice.
            if (!window.closed && window.history.length > 1) {
                window.history.back();
            }
        }, 150);

        return false;
    }

    // 2. If opened in same tab with history back to index.html
    if (window.history.length > 1) {
        window.history.back();
        return false;
    }

    // 3. Fallback: No active opener window and no history stack, safely navigate to portal
    window.location.href = './index.html' + cleanHash;
    return false;
};

// Auto-bind to all links targeting index.html on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    try {
        const portalLinks = document.querySelectorAll('a[href*="index.html"]');
        portalLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                const href = link.getAttribute('href') || '';
                const hash = href.includes('#') ? '#' + href.split('#')[1] : '';
                window.backToMainPortal(e, hash);
            });
        });
    } catch (err) {}
});

