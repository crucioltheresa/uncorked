// US-16 Add to Wishlist / US-17 View and Manage Wishlist: favourite buttons
const { favouriteState } = require('../static/js/wishlist');

describe('favouriteState (card star)', () => {
    test('in favourites: filled star, pressed, "Remove" label', () => {
        expect(favouriteState(true, 'Etna Bianco')).toEqual({
            pressed: 'true',
            label: 'Remove Etna Bianco from favourites',
            iconClass: 'bi bi-star-fill',
            text: 'Remove from favourites',
            activeClass: true,
        });
    });

    test('not in favourites: outline star, not pressed, "Add" label', () => {
        const state = favouriteState(false, 'Etna Bianco');
        expect(state.pressed).toBe('false');
        expect(state.label).toBe('Add Etna Bianco to favourites');
        expect(state.iconClass).toBe('bi bi-star');
        expect(state.activeClass).toBe(false);
    });
});

describe('favouriteState (wine page button)', () => {
    test('in favourites: X icon and "Remove from favourites"', () => {
        const state = favouriteState(true, 'Etna Bianco', 'detail');
        expect(state.iconClass).toBe('bi bi-x-lg');
        expect(state.text).toBe('Remove from favourites');
    });

    test('not in favourites: star icon and "Add to favourites"', () => {
        const state = favouriteState(false, 'Etna Bianco', 'detail');
        expect(state.iconClass).toBe('bi bi-star');
        expect(state.text).toBe('Add to favourites');
    });
});
