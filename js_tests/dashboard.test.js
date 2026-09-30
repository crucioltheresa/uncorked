// US-09 / US-15 Store Dashboard: the mobile section tab bar
const { tabScrollLeft } = require('../static/js/dashboard');

describe('tabScrollLeft', () => {
    test('centres a tab in the middle of the bar', () => {
        // Tab at 400px, 100px wide, bar 300px wide, 1000px to scroll
        expect(tabScrollLeft(400, 100, 300, 1000)).toBe(300);
    });

    test('never scrolls before the start', () => {
        expect(tabScrollLeft(20, 100, 300, 1000)).toBe(0);
    });

    test('never scrolls past the end', () => {
        expect(tabScrollLeft(900, 100, 300, 1000)).toBe(700);
    });

    test('no scrolling when everything fits', () => {
        expect(tabScrollLeft(200, 100, 600, 600)).toBe(0);
    });
});
