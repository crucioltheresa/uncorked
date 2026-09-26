from .utils import get_countries_with_wine_counts


def countries(request):
    """Provide list of countries with wines to all templates."""
    return {
        'countries': get_countries_with_wine_counts()
    }
