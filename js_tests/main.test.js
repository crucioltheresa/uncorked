// US-26 Homepage: the rotating promo bar and the Back button
const {
    nextPromoIndex, shouldRotatePromo, referrerIsSameSite,
} = require('../static/js/main');

describe('shouldRotatePromo', () => {
    test('rotates several messages for everyone else', () => {
        expect(shouldRotatePromo(2, false)).toBe(true);
    });

    test('stops for users who prefer reduced motion', () => {
        expect(shouldRotatePromo(2, true)).toBe(false);
    });

    test('nothing to rotate with a single message', () => {
        expect(shouldRotatePromo(1, false)).toBe(false);
    });
});

describe('nextPromoIndex', () => {
    test('moves to the next message', () => {
        expect(nextPromoIndex(0, 2)).toBe(1);
    });

    test('wraps back to the first message', () => {
        expect(nextPromoIndex(1, 2)).toBe(0);
        expect(nextPromoIndex(2, 3)).toBe(0);
    });
});

describe('referrerIsSameSite', () => {
    test('true when the previous page was on this site', () => {
        expect(referrerIsSameSite('https://uncorked.ie/wines/', 'uncorked.ie'))
            .toBe(true);
    });

    test('false for another site or no referrer', () => {
        expect(referrerIsSameSite('https://other.example/', 'uncorked.ie'))
            .toBe(false);
        expect(referrerIsSameSite('', 'uncorked.ie')).toBe(false);
    });
});
