// US-11 View and Manage Cart: quantity updates on the cart page
const {
    parseCartQuantity, cartTriggerLabels, cartStatusClass, CART_UPDATE_DELAY,
} = require('../static/js/cart');

describe('parseCartQuantity', () => {
    test('whole numbers are accepted', () => {
        expect(parseCartQuantity('3')).toBe(3);
        expect(parseCartQuantity(' 12 ')).toBe(12);
        expect(parseCartQuantity(5)).toBe(5);
    });

    test('0 is valid (it removes the wine)', () => {
        expect(parseCartQuantity('0')).toBe(0);
    });

    test('empty, negative, decimal and text values are rejected', () => {
        ['', '  ', '-1', '2.5', 'abc', '1e3'].forEach((value) => {
            expect(parseCartQuantity(value)).toBeNull();
        });
    });
});

describe('cartTriggerLabels', () => {
    test('several bottles', () => {
        expect(cartTriggerLabels(3)).toEqual({
            trigger: 'Your cart, 3 bottles',
            badge: '3 bottles in your cart',
        });
    });

    test('one bottle is singular', () => {
        expect(cartTriggerLabels(1).trigger).toBe('Your cart, 1 bottle');
        expect(cartTriggerLabels(1).badge).toBe('1 bottle in your cart');
    });

    test('empty cart has no count in the icon label', () => {
        expect(cartTriggerLabels(0).trigger).toBe('Your cart');
    });
});

describe('cartStatusClass', () => {
    test('uses the flash message style for the level', () => {
        expect(cartStatusClass('warning')).toBe('cart__status message message--warning');
        expect(cartStatusClass('error')).toBe('cart__status message message--error');
    });
});

test('updates wait a short moment after the last change', () => {
    expect(CART_UPDATE_DELAY).toBeGreaterThan(0);
    expect(CART_UPDATE_DELAY).toBeLessThanOrEqual(1000);
});
