// US-11 View and Manage Cart: the nav cart preview
const {
    focusLeftPreview,
    CART_PREVIEW_CLOSE_DELAY,
} = require('../static/js/cart_preview');

describe('focusLeftPreview', () => {
    test('stays open while focus moves inside the preview', () => {
        expect(focusLeftPreview(true, true)).toBe(false);
    });

    test('closes when focus moves outside the preview', () => {
        expect(focusLeftPreview(false, true)).toBe(true);
    });

    test('closes when focus goes nowhere (the window lost focus)', () => {
        expect(focusLeftPreview(false, false)).toBe(true);
    });
});

describe('close delay', () => {
    test('leaves time to move the mouse into the panel', () => {
        expect(CART_PREVIEW_CLOSE_DELAY).toBeGreaterThanOrEqual(150);
        expect(CART_PREVIEW_CLOSE_DELAY).toBeLessThanOrEqual(500);
    });
});
