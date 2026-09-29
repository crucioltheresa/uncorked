// Pure helpers (no DOM), exported for tests

// Next promo message to show, wrapping back to the first
function nextPromoIndex(current, count) {
    return (current + 1) % count;
}

// True when the previous page was on this site (so Back can use history)
function referrerIsSameSite(referrer, host) {
    return Boolean(referrer) && new URL(referrer).host === host;
}

// Promo bar slider: Rotates between promotional messages every 3 seconds
function initPromoBar() {
    const promoEl = document.getElementById('promoText');
    if (!promoEl) return;

    // Messages come from the pricing rules, rendered by base.html
    const messagesEl = document.getElementById('promoMessages');
    const promoMessages = messagesEl ? JSON.parse(messagesEl.textContent) : [];
    if (promoMessages.length === 0) return;

    let currentPromo = 0;

    function updatePromo() {
        promoEl.style.opacity = '0';
        promoEl.style.transform = 'translateX(20px)';

        setTimeout(() => {
            currentPromo = nextPromoIndex(currentPromo, promoMessages.length);
            promoEl.textContent = promoMessages[currentPromo];
            promoEl.style.opacity = '1';
            promoEl.style.transform = 'translateX(0)';
        }, 400);
    }

    // Set initial message with visible opacity
    promoEl.textContent = promoMessages[0];
    promoEl.style.opacity = '1';
    promoEl.style.transform = 'translateX(0)';
    setInterval(updatePromo, 3000);
}

// Browser only from here (the file can also be loaded by tests in Node)
if (typeof document !== 'undefined') {

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPromoBar);
} else {
    initPromoBar();
}

// Mobile hamburger menu: Toggles category menu open/closed
(function() {
    const hamburgerBtn = document.querySelector('.nav__hamburger');
    const categoryMenu = document.getElementById('navCategories');
    const categoryLinks = document.querySelectorAll('.nav__category');

    if (!hamburgerBtn || !categoryMenu) return;

    // Toggle menu open/closed
    function toggleMenu() {
        const isOpen = categoryMenu.classList.contains('nav__categories--open');
        if (isOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }

    // Open menu: add open class and update icon/aria
    function openMenu() {
        categoryMenu.classList.add('nav__categories--open');
        hamburgerBtn.setAttribute('aria-expanded', 'true');

        // Replace list icon with X icon
        const icon = hamburgerBtn.querySelector('i');
        icon.classList.remove('bi-list');
        icon.classList.add('bi-x');
    }

    // Close menu: remove open class and update icon/aria
    function closeMenu() {
        categoryMenu.classList.remove('nav__categories--open');
        hamburgerBtn.setAttribute('aria-expanded', 'false');

        // Replace X icon with list icon
        const icon = hamburgerBtn.querySelector('i');
        icon.classList.remove('bi-x');
        icon.classList.add('bi-list');
    }

    // Click hamburger to toggle menu
    hamburgerBtn.addEventListener('click', toggleMenu);

    // Close menu when category link is clicked (but not summary elements)
    categoryLinks.forEach(link => {
        // Skip summary elements - they're handled by details/summary native behavior
        if (link.tagName !== 'SUMMARY') {
            link.addEventListener('click', closeMenu);
        }
    });

    // Close menu when a country link inside details is clicked
    const countryLinks = document.querySelectorAll('.nav__country-group--mobile .nav__country-link');
    countryLinks.forEach(link => {
        link.addEventListener('click', closeMenu);
    });

    // Close menu on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && categoryMenu.classList.contains('nav__categories--open')) {
            closeMenu();
        }
    });

    // Close menu on window resize past tablet breakpoint (768px)
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 768) {
            closeMenu();
        }
    });
})();

// Desktop Country dropdown: Toggle, keyboard, and outside click handling
(function() {
    const countryToggle = document.getElementById('countryToggle');
    const countryDropdown = document.getElementById('countryDropdown');
    const countryLinks = document.querySelectorAll('.nav__country-group--desktop .nav__country-link');

    if (!countryToggle || !countryDropdown) return;

    // Toggle dropdown
    function toggleCountryDropdown() {
        const isOpen = countryToggle.getAttribute('aria-expanded') === 'true';
        if (isOpen) {
            closeCountryDropdown();
        } else {
            openCountryDropdown();
        }
    }

    // Open dropdown
    function openCountryDropdown() {
        countryToggle.setAttribute('aria-expanded', 'true');
        countryDropdown.classList.add('nav__country-dropdown--open');
    }

    // Close dropdown
    function closeCountryDropdown() {
        countryToggle.setAttribute('aria-expanded', 'false');
        countryDropdown.classList.remove('nav__country-dropdown--open');
    }

    // Toggle on button click
    countryToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleCountryDropdown();
    });

    // Close when a country is clicked
    countryLinks.forEach(link => {
        link.addEventListener('click', closeCountryDropdown);
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && countryToggle.getAttribute('aria-expanded') === 'true') {
            closeCountryDropdown();
        }
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
        const isClickInside = countryToggle.contains(e.target) || countryDropdown.contains(e.target);
        if (!isClickInside && countryToggle.getAttribute('aria-expanded') === 'true') {
            closeCountryDropdown();
        }
    });
})();

}

// Back button: Navigate to previous page or homepage
function goBack() {
    if (referrerIsSameSite(document.referrer, window.location.host)) {
        window.history.back();
    } else {
        window.location.href = '/';
    }
    return false;
}

if (typeof document !== 'undefined') {

// Sommelier chat widget: Floating button, dialog, and page integration
(function() {
    const floatBtn = document.getElementById('sommelierFloatBtn');
    const dialog = document.getElementById('sommelierDialog');
    const closeBtn = document.getElementById('sommelierCloseBtn');
    const restartBtn = document.getElementById('sommelierRestartBtn');

    if (!floatBtn || !dialog) return;

    let chatController = null;

    function openDialog() {
        dialog.hidden = false;
        dialog.focus();
        // Give focus to first button or element in chat
        setTimeout(() => {
            const firstButton = dialog.querySelector('.chat-option');
            if (firstButton) firstButton.focus();
        }, 100);
    }

    function closeDialog() {
        dialog.hidden = true;
        floatBtn.focus();
    }

    floatBtn.addEventListener('click', openDialog);
    closeBtn.addEventListener('click', closeDialog);

    // Handle Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !dialog.hidden) {
            closeDialog();
        }
    });

    // Load sommelier_chat.js and initialize
    const script = document.createElement('script');
    script.src = '/static/js/sommelier_chat.js';
    script.onload = function() {
        chatController = window.initSommelierChat('sommelier-dialog-chat', window.SOMMELIER_QUESTIONS);
        restartBtn.addEventListener('click', () => {
            chatController.restartQuiz();
        });
    };
    document.head.appendChild(script);

    // Progressive enhancement: intercept "Ask the Sommelier" button
    document.addEventListener('click', (e) => {
        if (e.target.closest('a[href="/sommelier/"]')) {
            e.preventDefault();
            openDialog();
        }
    });
})();

}

if (typeof module !== "undefined") {
    module.exports = { nextPromoIndex, referrerIsSameSite };
}
