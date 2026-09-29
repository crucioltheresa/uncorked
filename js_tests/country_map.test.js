// US-29 Explore by Country: the clickable world map
const {
    buildIsoMap,
    isCountryClickable,
    countryAriaLabel,
    wineCountLabel,
    countryFilterUrl,
} = require('../static/js/country_map');

const countries = [
    { name: 'France', iso_code: 'FRA', wine_count: 2 },
    { name: 'Spain', iso_code: 'ESP', wine_count: 1 },
];

describe('buildIsoMap', () => {
    test('looks countries up by ISO code', () => {
        const isoMap = buildIsoMap(countries);
        expect(isoMap.FRA.name).toBe('France');
        expect(isoMap.ESP.wine_count).toBe(1);
    });
});

describe('isCountryClickable', () => {
    const isoMap = buildIsoMap(countries);

    test('countries with wines are clickable', () => {
        expect(isCountryClickable('FRA', isoMap)).toBe(true);
    });

    test('countries without wines are not', () => {
        expect(isCountryClickable('ATL', isoMap)).toBe(false);
    });
});

describe('labels and links', () => {
    test('aria-label names the country and its wines', () => {
        expect(countryAriaLabel(countries[0])).toBe('France: 2 wines');
    });

    test('tooltip uses singular and plural', () => {
        expect(wineCountLabel(1)).toBe('1 wine');
        expect(wineCountLabel(3)).toBe('3 wines');
    });

    test('filter URL encodes the country name', () => {
        expect(countryFilterUrl('/wines/', 'New Zealand'))
            .toBe('/wines/?country=New%20Zealand');
    });
});
