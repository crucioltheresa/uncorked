// Favourite stars on wine cards.
// Each star is a POST form that works without JavaScript. With JavaScript,
// the form is sent with fetch so the page doesn't reload: the star, its
// label and aria-pressed are updated, and a short message is shown.

/**
 * Everything the star button needs for a given state. Pure, so it can be
 * tested without a browser.
 * @param {boolean} inWishlist - whether the wine is now in the wishlist
 * @param {string} wineName
 * @returns {{pressed: string, label: string, iconClass: string, activeClass: boolean}}
 */
function favouriteState(inWishlist, wineName) {
    return {
        pressed: inWishlist ? 'true' : 'false',
        label: inWishlist
            ? `Remove ${wineName} from favourites`
            : `Add ${wineName} to favourites`,
        iconClass: inWishlist ? 'bi bi-star-fill' : 'bi bi-star',
        activeClass: inWishlist,
    };
}

// Show the star as in or out of the wishlist
function applyFavouriteState(button, inWishlist) {
    const state = favouriteState(inWishlist, button.dataset.wineName);
    button.setAttribute('aria-pressed', state.pressed);
    button.setAttribute('aria-label', state.label);
    button.classList.toggle('favourite-star__button--active', state.activeClass);
    const icon = button.querySelector('i');
    if (icon) icon.className = state.iconClass;
}

// Small message that fades out; role="status" so screen readers hear it
function showFavouriteMessage(text, isError) {
    let toast = document.getElementById('favouriteToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'favouriteToast';
        toast.className = 'favourite-toast';
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');
        document.body.appendChild(toast);
    }
    toast.textContent = text;
    toast.classList.toggle('favourite-toast--error', Boolean(isError));
    toast.classList.add('favourite-toast--visible');
    clearTimeout(toast.hideTimer);
    toast.hideTimer = setTimeout(() => {
        toast.classList.remove('favourite-toast--visible');
    }, 2500);
}

async function handleFavouriteSubmit(event) {
    const form = event.target.closest('[data-favourite-form]');
    if (!form) return;
    event.preventDefault();

    const button = form.querySelector('button');
    const wasInWishlist = button.getAttribute('aria-pressed') === 'true';
    button.disabled = true;

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
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        applyFavouriteState(button, data.in_wishlist);
        // Update a nav favourites count if the page has one
        document.querySelectorAll('[data-wishlist-count]').forEach((el) => {
            el.textContent = data.count;
        });
        showFavouriteMessage(data.message, false);
    } catch (error) {
        // Keep the previous state and tell the user
        applyFavouriteState(button, wasInWishlist);
        showFavouriteMessage('Sorry, we couldn\'t update your favourites. Please try again.', true);
    } finally {
        button.disabled = false;
    }
}

if (typeof document !== 'undefined') {
    document.addEventListener('submit', handleFavouriteSubmit);
}

if (typeof module !== 'undefined') {
    module.exports = { favouriteState };
}
