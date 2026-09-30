// US-18 Write a Review / US-03 Profile & Order History: reviewing from
// the order page and editing from the profile's My Reviews
const {
    reviewButtonLabel,
    reviewStarClasses,
    reviewErrors,
} = require('../static/js/reviews_modal');

describe('reviewButtonLabel', () => {
    test('"Edit your review" once the wine is reviewed', () => {
        expect(reviewButtonLabel(true)).toBe('Edit your review');
    });

    test('"Write a review" before that', () => {
        expect(reviewButtonLabel(false)).toBe('Write a review');
    });
});

describe('reviewErrors', () => {
    test('keeps field errors that have messages', () => {
        const data = {
            ok: false,
            form_errors: [],
            errors: { title: ['This field is required.'], body: [] },
        };
        expect(reviewErrors(data)).toEqual({
            formErrors: [],
            fieldErrors: { title: ['This field is required.'] },
        });
    });

    test('passes form-wide errors through', () => {
        const data = {
            ok: false,
            form_errors: ['You have already reviewed this wine.'],
            errors: {},
        };
        expect(reviewErrors(data).formErrors)
            .toEqual(['You have already reviewed this wine.']);
    });

    test('anything unexpected becomes a generic error', () => {
        expect(reviewErrors(null).formErrors[0]).toMatch(/something went wrong/i);
    });
});

describe('reviewStarClasses', () => {
    test('fills stars up to the rating', () => {
        expect(reviewStarClasses(3)).toEqual([
            'bi bi-star-fill', 'bi bi-star-fill', 'bi bi-star-fill',
            'bi bi-star', 'bi bi-star',
        ]);
    });

    test('five stars are all filled', () => {
        expect(reviewStarClasses(5).every((c) => c === 'bi bi-star-fill'))
            .toBe(true);
    });
});
