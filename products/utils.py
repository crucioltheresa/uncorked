from django.db.models import Count, Q
from .models import Wine

COUNTRY_ISO_CODE_MAP = {
    'Argentina': 'ARG',
    'Australia': 'AUS',
    'Belgium': 'BEL',
    'Brazil': 'BRA',
    'Czech Republic': 'CZE',
    'Denmark': 'DNK',
    'France': 'FRA',
    'Germany': 'DEU',
    'Greece': 'GRC',
    'Italy': 'ITA',
    'New Zealand': 'NZL',
    'Portugal': 'PRT',
    'Slovenia': 'SVN',
    'South Africa': 'ZAF',
    'Spain': 'ESP',
    'Switzerland': 'CHE',
    'Turkey': 'TUR',
    'USA': 'USA',
}


def get_countries_with_wine_counts():
    countries = (
        Wine.objects
        .values('region__country')
        .annotate(count=Count('id'))
        .order_by('region__country')
    )

    result = []
    for item in countries:
        country = item['region__country']
        iso_code = COUNTRY_ISO_CODE_MAP.get(country)

        if iso_code:
            result.append({
                'name': country,
                'iso_code': iso_code,
                'wine_count': item['count'],
            })

    result.sort(key=lambda x: x['name'])
    return result
