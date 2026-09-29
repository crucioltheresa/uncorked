// US-26 Homepage: the new arrivals and reviews carousels
const {
    carouselIndex,
    carouselButtonState,
    carouselDotStates,
    nextCarouselIndex,
    prevCarouselIndex,
} = require('../static/js/carousel');

describe('carouselIndex', () => {
    test('rounds the scroll position to the nearest item', () => {
        expect(carouselIndex(0, 316)).toBe(0);
        expect(carouselIndex(316, 316)).toBe(1);
        expect(carouselIndex(470, 316)).toBe(1);
        expect(carouselIndex(480, 316)).toBe(2);
    });
});

describe('carouselButtonState', () => {
    test('disables prev on the first item', () => {
        expect(carouselButtonState(0, 5))
            .toEqual({ prevDisabled: true, nextDisabled: false });
    });

    test('disables next on the last item', () => {
        expect(carouselButtonState(4, 5))
            .toEqual({ prevDisabled: false, nextDisabled: true });
    });

    test('enables both in the middle', () => {
        expect(carouselButtonState(2, 5))
            .toEqual({ prevDisabled: false, nextDisabled: false });
    });
});

describe('carouselDotStates', () => {
    test('only the current dot is active', () => {
        expect(carouselDotStates(4, 1)).toEqual([false, true, false, false]);
    });
});

describe('next / prev index', () => {
    test('next moves forward and stops at the last item', () => {
        expect(nextCarouselIndex(0, 3)).toBe(1);
        expect(nextCarouselIndex(2, 3)).toBeNull();
    });

    test('prev moves back and stops at the first item', () => {
        expect(prevCarouselIndex(2)).toBe(1);
        expect(prevCarouselIndex(0)).toBeNull();
    });
});
