/**
 * APH Portal - Intelligent Navigation & Subpage Return Handler
 * Guarantees that "Back to Main Portal" returns to the already-opened
 * portal tab rather than opening duplicate tabs.
 */

window.backToMainPortal = function(e, targetHash) {
    if (e && e.preventDefault) {
        e.preventDefault();
    }

    // 1. If opened from an active opener window (e.g. main portal tab)
    if (window.opener && !window.opener.closed) {
        try {
            if (targetHash && window.opener.location) {
                const cleanHash = targetHash.startsWith('#') ? targetHash : '#' + targetHash;
                const base = window.opener.location.href.split('#')[0];
                window.opener.location.replace(base + cleanHash);
            }
            window.opener.focus();
        } catch (err) {}
        try {
            window.close();
            return false;
        } catch (err) {}
    }

    // 2. Try closing window directly (works if opened via script or target="_blank")
    try {
        window.close();
    } catch (err) {}

    // 3. Fallback: if window did not close within 100ms
    setTimeout(function() {
        if (!window.closed) {
            // If user navigated within this same tab from index.html
            if (window.history.length > 1 && document.referrer && document.referrer.includes('index.html')) {
                window.history.back();
            } else {
                // Focus existing named main portal window if it exists, or navigate
                try {
                    const cleanHash = targetHash ? (targetHash.startsWith('#') ? targetHash : '#' + targetHash) : '';
                    const targetUrl = './index.html' + cleanHash;
                    const portalWin = window.open(targetUrl, 'aph_main_portal');
                    if (portalWin) {
                        try { portalWin.focus(); } catch (err) {}
                    }
                    try { window.close(); } catch (err) {}
                } catch (err) {
                    window.location.href = './index.html' + (targetHash || '');
                }
            }
        }
    }, 100);

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

