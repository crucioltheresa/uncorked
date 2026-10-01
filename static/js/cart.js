// Cart page quantities (US-11). Each row has a quantity stepper in a POST
// form with an Update button, which works without JavaScript. With
// JavaScript the button is hidden and changes are sent with fetch a moment
// after the user stops changing the number. The line total, the totals
// (including the 8-bottle discount), the nav badge and the cart preview are
// refreshed, and the result is announced in the page's role="status" line.

// Wait this long after the last change before sending it
const CART_UPDATE_DELAY = 500;

/**
 * The quantity typed in a stepper as a whole number, or null if it isn't
 * one (empty, negative, decimal or text). 0 is valid: it removes the wine.
 * @param {string|number} raw
 * @returns {number|null}
 */
function parseCartQuantity(raw) {
    const text = String(raw).trim();
    if (!/^\d+$/.test(text)) return null;
    return Number(text);
}

/**
 * Labels for the nav cart icon and its badge for a number of bottles.
 * @param {number} count - bottles in the cart
 * @returns {{trigger: string, badge: string}}
 */
function cartTriggerLabels(count) {
    const bottles = `${count} bottle${count === 1 ? '' : 's'}`;
    return {
        trigger: count ? `Your cart, ${bottles}` : 'Your cart',
        badge: `${bottles} in your cart`,
    };
}

/**
 * Classes for the status line, matching the site's flash messages.
 * @param {string} level - "success", "warning" or "error"
 * @returns {string}
 */
function cartStatusClass(level) {
    return `cart__status message message--${level}`;
}

(function () {
    if (typeof document === 'undefined') return;
    const forms = document.querySelectorAll('[data-cart-update]');
    if (!forms.length) return;

    const status = document.querySelector('[data-cart-status]');
    const totalsBox = document.querySelector('[data-cart-totals]');
    const contents = document.querySelector('[data-cart-contents]');
    const empty = document.querySelector('[data-cart-empty]');
    // Updates are sent one at a time: the cart lives in the session, so two
    // requests at once could overwrite each other's change
    let queue = Promise.resolve();

    // Clear first so the same message twice is still announced
    function announce(message, level) {
        status.textContent = '';
        status.className = cartStatusClass(level);
        setTimeout(() => {
            status.textContent = message;
        }, 50);
    }

    // Nav icon: badge number and labels; the badge goes when the cart empties
    function updateBadge(count) {
        const trigger = document.querySelector('.cart-preview__trigger');
        if (!trigger) return;
        const labels = cartTriggerLabels(count);
        trigger.setAttribute('aria-label', labels.trigger);
        let badge = trigger.querySelector('.nav__icon-count');
        if (!count) {
            if (badge) badge.remove();
            return;
        }
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'nav__icon-count';
            trigger.appendChild(badge);
        }
        badge.textContent = count;
        badge.setAttribute('aria-label', labels.badge);
    }

    // A removed row takes focus with it, so move focus somewhere sensible
    function removeRow(row) {
        const hadFocus = row.contains(document.activeElement);
        const nextRow = row.nextElementSibling || row.previousElementSibling;
        row.remove();
        if (!hadFocus) return;
        const target = nextRow
            ? nextRow.querySelector('[data-cart-quantity]')
            : empty.querySelector('a');
        if (target) target.focus();
    }

    // Show the server's answer: the row, the totals, the badge and a message
    function applyResult(form, data) {
        const row = form.closest('[data-cart-row]');
        const input = form.querySelector('[data-cart-quantity]');
        form.dataset.quantity = String(data.quantity);

        if (data.quantity === 0) {
            removeRow(row);
        } else {
            // Don't overwrite a newer change the user is still making
            if (!form.updateTimer) input.value = data.quantity;
            input.max = data.max;
            row.querySelector('[data-cart-line-total]').textContent = `€${data.line_total}`;
        }

        totalsBox.innerHTML = data.totals_html;
        updateBadge(data.bottle_count);
        if (!data.bottle_count) {
            contents.hidden = true;
            empty.hidden = false;
        }
        announce(data.message, data.level);
        // Lets the nav cart preview reload its contents
        document.dispatchEvent(new CustomEvent('cart:updated'));
    }

    async function send(form) {
        const row = form.closest('[data-cart-row]');
        const input = form.querySelector('[data-cart-quantity]');
        if (!row.isConnected) return;

        const quantity = parseCartQuantity(input.value);
        if (quantity === null) {
            input.value = form.dataset.quantity;
            announce('Please enter a whole number of bottles (0 removes the wine).', 'error');
            return;
        }
        if (String(quantity) === form.dataset.quantity) return;

        row.classList.add('cart__row--updating');
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    Accept: 'application/json',
                },
                credentials: 'same-origin',
            });
            // Rejected values (400) still come back as JSON with the cart
            // as it is, so the row and totals can be put back
            let data = null;
            try {
                data = await response.json();
            } catch (error) {
                data = null;
            }
            if (!data) throw new Error(`HTTP ${response.status}`);
            applyResult(form, data);
        } catch (error) {
            if (!form.updateTimer) input.value = form.dataset.quantity;
            announce('Sorry, we couldn\'t update your cart. Please try again.', 'error');
        } finally {
            row.classList.remove('cart__row--updating');
        }
    }

    function sendNow(form) {
        clearTimeout(form.updateTimer);
        form.updateTimer = null;
        queue = queue.then(() => send(form));
    }

    function schedule(form) {
        clearTimeout(form.updateTimer);
        form.updateTimer = setTimeout(() => sendNow(form), CART_UPDATE_DELAY);
    }

    forms.forEach((form) => {
        const input = form.querySelector('[data-cart-quantity]');
        // The last quantity the server confirmed
        form.dataset.quantity = input.value;
        form.querySelector('[data-cart-update-button]').hidden = true;

        // Typing: wait for a pause; an empty box means the user is mid-edit
        input.addEventListener('input', () => {
            if (input.value === '') {
                clearTimeout(form.updateTimer);
                form.updateTimer = null;
            } else {
                schedule(form);
            }
        });
        // Leaving the box empty puts the last quantity back
        input.addEventListener('change', () => {
            if (input.value === '') input.value = form.dataset.quantity;
        });

        // − and + change the value inline (stepDown/stepUp), which doesn't
        // fire an input event, so listen for their clicks too
        form.querySelectorAll('.quantity-stepper button').forEach((button) => {
            button.addEventListener('click', () => schedule(form));
        });

        // Enter in the box sends straight away
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            sendNow(form);
        });
    });
})();

if (typeof module !== 'undefined') {
    module.exports = {
        parseCartQuantity, cartTriggerLabels, cartStatusClass, CART_UPDATE_DELAY,
    };
}
