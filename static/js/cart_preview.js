// Nav cart preview: a small panel under the cart icon listing what's in the
// cart. Opens on hover (devices that can hover) and on keyboard focus; the
// contents are fetched from /cart/preview/ the first time it opens, so pages
// don't do extra queries. On touch screens the icon is just a link.

// Time to move the mouse from the icon into the panel before it closes
const CART_PREVIEW_CLOSE_DELAY = 250;

/**
 * Whether focus has left the preview (so it should close). Pure: takes the
 * container's contains() result instead of touching the DOM.
 * @param {boolean} containsNewFocus - container.contains(relatedTarget)
 * @param {boolean} hasNewFocus - relatedTarget is not null
 * @returns {boolean}
 */
function focusLeftPreview(containsNewFocus, hasNewFocus) {
    return !hasNewFocus || !containsNewFocus;
}

(function () {
    if (typeof document === 'undefined') return;
    const container = document.querySelector('[data-cart-preview]');
    if (!container) return;

    const trigger = container.querySelector('.cart-preview__trigger');
    const panel = container.querySelector('.cart-preview__panel');
    const canHover = window.matchMedia('(hover: hover)').matches;
    let loaded = false;
    let closeTimer = null;
    // Set while Escape returns focus to the icon, so it doesn't reopen
    let skipFocusOpen = false;

    // Fetch the fragment once; cart_updated events mark it stale
    async function loadContents() {
        if (loaded) return;
        loaded = true;
        panel.innerHTML = '<p class="cart-preview__loading">Loading…</p>';
        try {
            const response = await fetch(container.dataset.url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin',
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            panel.innerHTML = await response.text();
        } catch (error) {
            loaded = false;
            panel.innerHTML = '<p class="cart-preview__loading">Couldn\'t load your cart. <a href="'
                + trigger.getAttribute('href') + '">View cart</a></p>';
        }
    }

    function open() {
        clearTimeout(closeTimer);
        if (!panel.hidden) return;
        panel.hidden = false;
        trigger.setAttribute('aria-expanded', 'true');
        loadContents();
    }

    function close() {
        clearTimeout(closeTimer);
        panel.hidden = true;
        trigger.setAttribute('aria-expanded', 'false');
    }

    function closeSoon() {
        clearTimeout(closeTimer);
        closeTimer = setTimeout(close, CART_PREVIEW_CLOSE_DELAY);
    }

    // Hover: only where a real pointer can hover (not touch screens)
    if (canHover) {
        container.addEventListener('mouseenter', open);
        container.addEventListener('mouseleave', closeSoon);
    }

    // Keyboard: open when the icon gets focus, close when focus leaves
    trigger.addEventListener('focus', () => {
        if (canHover && !skipFocusOpen) open();
        skipFocusOpen = false;
    });
    container.addEventListener('focusout', (event) => {
        const next = event.relatedTarget;
        if (focusLeftPreview(Boolean(next) && container.contains(next), Boolean(next))) {
            closeSoon();
        }
    });

    // Escape closes and puts focus back on the icon
    container.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !panel.hidden) {
            close();
            skipFocusOpen = document.activeElement !== trigger;
            trigger.focus();
        }
    });

    // Anything that adds to the cart without a reload can dispatch this
    document.addEventListener('cart:updated', () => {
        loaded = false;
        if (!panel.hidden) loadContents();
    });
})();

if (typeof module !== 'undefined') {
    module.exports = { focusLeftPreview, CART_PREVIEW_CLOSE_DELAY };
}
