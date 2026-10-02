// Checkout and payment (US-12 / US-13 / US-14). Both forms show a
// "Processing…" state while they work: the button is disabled (so an order
// or a payment can't be sent twice), a spinner appears and the change is
// announced to screen readers. If the payment fails, the button comes back
// with Stripe's error message.

/**
 * What the submit button shows in each state. Pure, so it can be tested
 * without a browser.
 * @param {boolean} processing - whether the form is being sent
 * @param {string} idleLabel - the button's normal text, e.g. "Pay €83.28"
 * @returns {{disabled: boolean, label: string, spinner: boolean, status: string}}
 */
function submitButtonState(processing, idleLabel) {
    if (processing) {
        return {
            disabled: true,
            label: 'Processing…',
            spinner: true,
            status: 'Processing, please wait.',
        };
    }
    return { disabled: false, label: idleLabel, spinner: false, status: '' };
}

// Show a state on a form's submit button and its status line
function applySubmitState(form, processing) {
    const button = form.querySelector('[data-submit-button]');
    const label = button.querySelector('[data-submit-label]');
    const spinner = button.querySelector('[data-submit-spinner]');
    const status = form.querySelector('[data-submit-status]');
    const state = submitButtonState(processing, button.dataset.idleLabel);
    button.disabled = state.disabled;
    form.setAttribute('aria-busy', processing ? 'true' : 'false');
    label.textContent = state.label;
    spinner.hidden = !state.spinner;
    if (status) status.textContent = state.status;
}

if (typeof document !== 'undefined') (function () {
    // Checkout: the form posts normally; just stop a second click from
    // creating a second order
    const checkoutForm = document.querySelector('[data-checkout-form]');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', (event) => {
            if (checkoutForm.getAttribute('aria-busy') === 'true') {
                event.preventDefault();
                return;
            }
            applySubmitState(checkoutForm, true);
        });
        // Coming back with the browser's Back button: show the normal button
        window.addEventListener('pageshow', () => applySubmitState(checkoutForm, false));
    }

    // Payment: Stripe confirms the card in the page
    const paymentForm = document.getElementById('payment-form');
    if (!paymentForm || typeof Stripe === 'undefined') return;

    const stripe = Stripe(paymentForm.dataset.stripeKey);
    const cardElement = stripe.elements().create('card');
    cardElement.mount('#card-element');
    const errors = document.getElementById('card-errors');

    paymentForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (paymentForm.getAttribute('aria-busy') === 'true') return;
        errors.textContent = '';
        applySubmitState(paymentForm, true);

        try {
            const { error, paymentIntent } = await stripe.confirmCardPayment(
                paymentForm.dataset.clientSecret,
                { payment_method: { card: cardElement } }
            );
            if (error) throw error;
            if (paymentIntent.status === 'succeeded') {
                // Stay in the processing state while the success page loads
                window.location.href = paymentForm.dataset.successUrl;
                return;
            }
            throw new Error('The payment was not completed. Please try again.');
        } catch (error) {
            errors.textContent = error.message ||
                'Sorry, the payment could not be completed. Please try again.';
            applySubmitState(paymentForm, false);
        }
    });
})();

if (typeof module !== 'undefined') {
    module.exports = { submitButtonState };
}
