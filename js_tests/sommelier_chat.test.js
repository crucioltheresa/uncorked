// US-20 Wine Quiz / US-21 Quiz Recommendations: the sommelier chat
const {
    buildSommelierPayload,
    isQuizComplete,
    parseCookie,
    wineDetailUrl,
} = require('../static/js/sommelier_chat');

describe('wineDetailUrl', () => {
    test('builds the wine page URL from the slug', () => {
        expect(wineDetailUrl('etna-bianco')).toBe('/wines/etna-bianco/');
    });

    test('encodes anything unsafe in the slug', () => {
        expect(wineDetailUrl('a b/c')).toBe('/wines/a%20b%2Fc/');
    });
});

describe('buildSommelierPayload', () => {
    test('wraps the answers the way /sommelier/submit/ expects', () => {
        const answers = { type: 'red', budget: '20to35' };
        expect(JSON.parse(buildSommelierPayload(answers))).toEqual({ answers });
    });

    test('an empty quiz sends empty answers', () => {
        expect(buildSommelierPayload({})).toBe('{"answers":{}}');
    });
});

describe('isQuizComplete', () => {
    test('complete once every question is answered', () => {
        expect(isQuizComplete(4, 5)).toBe(false);
        expect(isQuizComplete(5, 5)).toBe(true);
    });
});

describe('parseCookie', () => {
    test('reads the CSRF token among other cookies', () => {
        expect(parseCookie('sessionid=x; csrftoken=abc123', 'csrftoken'))
            .toBe('abc123');
    });

    test('decodes values and returns null when missing', () => {
        expect(parseCookie('name=a%20b', 'name')).toBe('a b');
        expect(parseCookie('', 'csrftoken')).toBeNull();
        expect(parseCookie('other=1', 'csrftoken')).toBeNull();
    });
});
