// US-12 Checkout / US-13 Payment / US-14 Payment failure: submit button states
const { submitButtonState } = require('../static/js/checkout');

describe('submitButtonState', () => {
    test('processing: disabled, "Processing…", spinner and a status message', () => {
        expect(submitButtonState(true, 'Pay €83.28')).toEqual({
            disabled: true,
            label: 'Processing…',
            spinner: true,
            status: 'Processing, please wait.',
        });
    });

    test('idle: enabled again with the original label and no spinner', () => {
        expect(submitButtonState(false, 'Pay €83.28')).toEqual({
            disabled: false,
            label: 'Pay €83.28',
            spinner: false,
            status: '',
        });
    });

    test('after a failed payment the button can be used again', () => {
        const processing = submitButtonState(true, 'Pay €20.00');
        const restored = submitButtonState(false, 'Pay €20.00');
        expect(processing.disabled).toBe(true);
        expect(restored.disabled).toBe(false);
        expect(restored.label).toBe('Pay €20.00');
    });

    test('the checkout button keeps its own label', () => {
        expect(submitButtonState(false, 'Continue to Payment').label)
            .toBe('Continue to Payment');
    });
});
