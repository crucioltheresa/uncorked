// Review modal on the order page and the profile's "My Reviews". Each
// "Write a review" / "Edit" link still works without JavaScript (it goes to
// the review page). With JavaScript it opens a Bootstrap modal, sends the
// form with fetch and, on success, turns every button for that wine into
// "Edit your review" and updates the review shown on the profile.

/**
 * Button text for a wine, depending on whether the user has reviewed it.
 * @param {boolean} hasReview
 * @returns {string}
 */
function reviewButtonLabel(hasReview) {
    return hasReview ? 'Edit your review' : 'Write a review';
}

/**
 * Icon classes for the five stars of a rating, e.g. 3 -> 3 filled, 2 empty.
 * @param {number} rating - 1 to 5
 * @returns {string[]}
 */
function reviewStarClasses(rating) {
    return [1, 2, 3, 4, 5].map(
        (star) => (star <= rating ? 'bi bi-star-fill' : 'bi bi-star')
    );
}

/**
 * Errors from the server's 400 JSON, ready to show in the modal.
 * Pure, so it can be tested without a browser.
 * @param {object|null} data - {form_errors: [], errors: {field: [...]}}
 * @returns {{formErrors: string[], fieldErrors: object}}
 */
function reviewErrors(data) {
    if (!data || (!data.errors && !data.form_errors)) {
        return {
            formErrors: ['Sorry, something went wrong. Please try again.'],
            fieldErrors: {},
        };
    }
    const fieldErrors = {};
    Object.entries(data.errors || {}).forEach(([name, messages]) => {
        if (messages && messages.length) fieldErrors[name] = messages;
    });
    return { formErrors: data.form_errors || [], fieldErrors };
}

function initReviewModal() {
    const modalEl = document.getElementById('reviewModal');
    if (!modalEl || typeof bootstrap === 'undefined') return;

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const form = modalEl.querySelector('[data-review-form]');
    const titleEl = document.getElementById('reviewModalTitle');
    const wineName = modalEl.querySelector('[data-review-wine]');
    const wineImage = modalEl.querySelector('[data-review-image]');
    const summary = document.getElementById('review-errors');
    const status = document.getElementById('reviewStatus');
    let trigger = null;

    function clearErrors() {
        modalEl.querySelectorAll('.form-error').forEach((el) => {
            el.textContent = '';
            el.hidden = true;
        });
        modalEl.querySelectorAll('[aria-invalid]').forEach((el) => {
            el.removeAttribute('aria-invalid');
        });
    }

    // Fill the modal from the button: wine, and any existing review
    function fillFrom(button) {
        const hasReview = Boolean(button.dataset.rating);
        titleEl.textContent = hasReview ? 'Edit your review' : 'Review this wine';
        wineName.textContent = button.dataset.wineName;
        wineImage.hidden = !button.dataset.wineImage;
        wineImage.src = button.dataset.wineImage || '';
        form.action = button.dataset.url;
        form.reset();
        const rating = form.querySelector(
            `input[name="rating"][value="${button.dataset.rating}"]`
        );
        if (rating) rating.checked = true;
        form.elements.title.value = button.dataset.title || '';
        form.elements.body.value = button.dataset.body || '';
        clearErrors();
    }

    // Show errors next to their fields (linked with aria-describedby)
    function showErrors(result) {
        if (result.formErrors.length) {
            summary.textContent = result.formErrors.join(' ');
            summary.hidden = false;
        }
        let firstInvalid = null;
        Object.entries(result.fieldErrors).forEach(([name, messages]) => {
            const errorEl = document.getElementById(`review-${name}-error`);
            if (errorEl) {
                errorEl.textContent = messages.join(' ');
                errorEl.hidden = false;
            }
            const input = form.querySelector(`[name="${name}"]`);
            if (input) {
                input.setAttribute('aria-invalid', 'true');
                firstInvalid = firstInvalid || input;
            }
        });
        (firstInvalid || summary).focus();
    }

    // After saving: every button for this wine now edits the review
    function updateButtons(review) {
        document.querySelectorAll(
            `[data-review-open][data-wine-id="${review.wine_id}"]`
        ).forEach((button) => {
            button.dataset.url = review.edit_url;
            button.dataset.rating = review.rating;
            button.dataset.title = review.title;
            button.dataset.body = review.body;
            button.href = `${review.edit_url}?next=${encodeURIComponent(window.location.pathname)}`;
            const label = button.querySelector('[data-review-label]');
            if (label) label.textContent = reviewButtonLabel(true);
            const icon = button.querySelector('i');
            if (icon) icon.className = 'bi bi-pencil';
        });
        updateReviewCard(review);
    }

    // Profile "My Reviews": show the edited review straight away
    function updateReviewCard(review) {
        const card = document.querySelector(`[data-review-card="${review.id}"]`);
        if (!card) return;
        card.querySelector('[data-review-title]').textContent = review.title;
        card.querySelector('[data-review-body]').textContent = review.body;
        const stars = card.querySelector('[data-review-stars]');
        stars.setAttribute('aria-label', `${review.rating} out of 5 stars`);
        stars.querySelectorAll('i').forEach((icon, index) => {
            icon.className = reviewStarClasses(review.rating)[index];
        });
        const verified = card.querySelector('[data-review-verified]');
        if (verified) verified.hidden = !review.verified_purchase;
    }

    document.addEventListener('click', (event) => {
        const button = event.target.closest('[data-review-open]');
        if (!button) return;
        event.preventDefault();
        trigger = button;
        fillFrom(button);
        modal.show();
    });

    // Focus goes to the rating (the checked star, or the first one)
    modalEl.addEventListener('shown.bs.modal', () => {
        const target = form.querySelector('input[name="rating"]:checked') ||
            form.querySelector('input[name="rating"]');
        target.focus();
    });

    // Focus goes back to the button that opened the modal
    modalEl.addEventListener('hidden.bs.modal', () => {
        if (trigger) trigger.focus();
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearErrors();
        const submit = form.querySelector('button[type="submit"]');
        submit.disabled = true;

        let response = null;
        let data = null;
        try {
            response = await fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    Accept: 'application/json',
                },
                credentials: 'same-origin',
            });
            data = await response.json();
        } catch (error) {
            // Network error or non-JSON reply: shown as a generic error
        }
        submit.disabled = false;

        if (response && response.ok && data && data.ok) {
            updateButtons(data.review);
            modal.hide();
            if (status) {
                status.textContent = data.message;
                status.hidden = false;
            }
        } else {
            showErrors(reviewErrors(data));
        }
    });
}

if (typeof document !== 'undefined') {
    // Wait for Bootstrap, which base.html loads after the page scripts
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initReviewModal);
    } else {
        initReviewModal();
    }
}

if (typeof module !== 'undefined') {
    module.exports = { reviewButtonLabel, reviewStarClasses, reviewErrors };
}
