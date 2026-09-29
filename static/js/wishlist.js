// Favourites: the star on wine cards, the "Add to / Remove from favourites"
// button on the wine page, and "Remove from favourites" on the favourites
// page. All are POST forms that work without JavaScript. With JavaScript
// they're sent with fetch so the page doesn't reload: the icon, text, label
// and aria-pressed are updated, and a short message is shown.

/**
 * Everything a favourite button needs for a given state. Pure, so it can be
 * tested without a browser.
 * @param {boolean} inWishlist - whether the wine is now in the wishlist
 * @param {string} wineName
 * @param {string} [variant] - "star" (card star) or "detail" (wine page)
 * @returns {{pressed: string, label: string, iconClass: string, text: string, activeClass: boolean}}
 */
function favouriteState(inWishlist, wineName, variant = 'star') {
    let iconClass = inWishlist ? 'bi bi-star-fill' : 'bi bi-star';
    if (variant === 'detail') {
        iconClass = inWishlist ? 'bi bi-x-lg' : 'bi bi-star';
    }
    return {
        pressed: inWishlist ? 'true' : 'false',
        label: inWishlist
            ? `Remove ${wineName} from favourites`
            : `Add ${wineName} to favourites`,
        iconClass,
        text: inWishlist ? 'Remove from favourites' : 'Add to favourites',
        activeClass: inWishlist,
    };
}

// Show a button as in or out of the wishlist
function applyFavouriteState(button, inWishlist) {
    const variant = button.dataset.favouriteToggle || 'star';
    const state = favouriteState(inWishlist, button.dataset.wineName, variant);
    button.setAttribute('aria-pressed', state.pressed);
    button.setAttribute('aria-label', state.label);
    const activeClass = variant === 'detail'
        ? 'wine-detail__wishlist--active'
        : 'favourite-star__button--active';
    button.classList.toggle(activeClass, state.activeClass);
    const icon = button.querySelector('i');
    if (icon) icon.className = state.iconClass;
    const text = button.querySelector('[data-favourite-text]');
    if (text) text.textContent = state.text;
}

// Favourites page: take the removed wine's card off the page
function removeFavouriteCard(form) {
    const card = form.closest('[data-favourite-card]');
    if (!card) return;
    const list = card.parentElement;
    card.remove();
    if (list && !list.querySelector('[data-favourite-card]')) {
        const empty = document.querySelector('[data-favourites-empty]');
        list.hidden = true;
        if (empty) empty.hidden = false;
    }
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
    // Either a favourites form, or the wine page button, which submits the
    // add-to-cart form to the toggle URL through formaction
    const submitter = event.submitter;
    const form = event.target.closest('[data-favourite-form]');
    const isDetailButton = Boolean(submitter && submitter.dataset.favouriteToggle);
    if (!form && !isDetailButton) return;
    event.preventDefault();

    const button = isDetailButton ? submitter : form.querySelector('button');
    const url = isDetailButton ? submitter.formAction : form.action;
    const wasInWishlist = button.getAttribute('aria-pressed') === 'true';
    button.disabled = true;

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: new FormData(event.target),
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                Accept: 'application/json',
            },
            credentials: 'same-origin',
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (form && form.hasAttribute('data-favourite-remove')) {
            if (!data.in_wishlist) removeFavouriteCard(form);
        } else {
            applyFavouriteState(button, data.in_wishlist);
        }
        // Update a nav favourites count if the page has one
        document.querySelectorAll('[data-wishlist-count]').forEach((el) => {
            el.textContent = data.count;
        });
        showFavouriteMessage(data.message, false);
    } catch (error) {
        // Keep the previous state and tell the user
        if (!(form && form.hasAttribute('data-favourite-remove'))) {
            applyFavouriteState(button, wasInWishlist);
        }
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
