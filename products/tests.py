from django.test import TestCase, Client
from django.urls import reverse
from .models import Wine, Region
from .utils import COUNTRY_ISO_CODE_MAP, get_countries_with_wine_counts


def create_test_wines():
    """Create four wines in three countries, plus a country with no wines."""
    france = Region.objects.create(
        name="Burgundy", slug="burgundy", country="France"
    )
    spain = Region.objects.create(name="Rioja", slug="rioja", country="Spain")
    italy = Region.objects.create(
        name="Tuscany", slug="tuscany", country="Italy"
    )
    Region.objects.create(name="Unknown", slug="unknown", country="Atlantis")

    Wine.objects.create(
        name="Wine 1", slug="wine-1", region=france,
        wine_type="red", price=25.0, character="Bold", is_available=True,
        producer="Producer 1", abv=13.5
    )
    Wine.objects.create(
        name="Wine 2", slug="wine-2", region=france,
        wine_type="white", price=20.0, character="Crisp", is_available=True,
        producer="Producer 2", abv=12.0
    )
    Wine.objects.create(
        name="Wine 3", slug="wine-3", region=spain,
        wine_type="red", price=30.0, character="Fruity", is_available=True,
        producer="Producer 3", abv=14.5
    )
    Wine.objects.create(
        name="Wine 4", slug="wine-4", region=italy,
        wine_type="red", price=28.0, character="Complex", is_available=True,
        producer="Producer 4", abv=14.0
    )


class HomepageWorldMapTests(TestCase):
    """US-29: World map on the homepage."""

    def setUp(self):
        self.client = Client()
        create_test_wines()

    def test_homepage_includes_world_map_and_countries(self):
        """US-29: homepage shows the world map and countries with wines."""
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/index.html')
        self.assertEqual(len(response.context['countries']), 3)
        self.assertContains(response, 'world-map')


class CountriesContextProcessorTests(TestCase):
    """US-29: Countries list available on every page."""

    def setUp(self):
        self.client = Client()
        create_test_wines()

    def test_context_processor_provides_countries(self):
        """US-29: only countries with wines are listed, alphabetically, with counts."""
        response = self.client.get(reverse('wine_list'))
        countries = response.context['countries']

        self.assertEqual(len(countries), 3)
        country_names = [c['name'] for c in countries]
        self.assertEqual(country_names, sorted(country_names))
        country_dict = {c['name']: c['wine_count'] for c in countries}
        self.assertEqual(country_dict['France'], 2)
        self.assertEqual(country_dict['Spain'], 1)
        self.assertEqual(country_dict['Italy'], 1)
        self.assertNotIn('Atlantis', country_names)

    def test_get_countries_with_wine_counts(self):
        """US-29: helper returns name, ISO code and wine count per country."""
        countries = get_countries_with_wine_counts()

        self.assertEqual(len(countries), 3)
        for country in countries:
            self.assertIn('name', country)
            self.assertIn('iso_code', country)
            self.assertIn('wine_count', country)
        country_dict = {c['name']: c for c in countries}
        self.assertEqual(country_dict['France']['wine_count'], 2)
        self.assertEqual(country_dict['France']['iso_code'], 'FRA')
        self.assertEqual(country_dict['Spain']['wine_count'], 1)
        self.assertEqual(country_dict['Spain']['iso_code'], 'ESP')

    def test_all_countries_in_database_have_iso_mapping(self):
        """US-29: every country with wines has an ISO code mapping."""
        countries = {wine.region.country for wine in Wine.objects.all()}
        for country in countries:
            self.assertIn(country, COUNTRY_ISO_CODE_MAP)


class CountryFilterTests(TestCase):
    """US-29: Filter the catalogue by country."""

    def setUp(self):
        self.client = Client()
        create_test_wines()

    def test_country_filter_returns_correct_wines(self):
        """US-29: country filter returns only that country's wines."""
        response = self.client.get(reverse('wine_list'), {'country': 'France'})
        wines = response.context['wines']

        self.assertEqual(wines.paginator.count, 2)
        names = [w.name for w in wines]
        self.assertIn('Wine 1', names)
        self.assertIn('Wine 2', names)

    def test_country_filter_case_insensitive(self):
        """US-29: country filter ignores letter case."""
        for value in ['france', 'FRANCE', 'FrAnCe']:
            response = self.client.get(reverse('wine_list'), {'country': value})
            self.assertEqual(response.context['wines'].paginator.count, 2)

    def test_country_filter_stacks_with_type_filter(self):
        """US-29: country filter combines with the type filter."""
        response = self.client.get(reverse('wine_list'), {
            'country': 'France',
            'type': 'red'
        })
        wines = response.context['wines']

        self.assertEqual(wines.paginator.count, 1)
        self.assertEqual(wines[0].name, 'Wine 1')
        self.assertEqual(wines[0].wine_type, 'red')


class WineSearchTests(TestCase):
    """US-08: Search the catalogue."""

    def setUp(self):
        self.client = Client()
        create_test_wines()

    def test_search_by_wine_name(self):
        """US-08: search by wine name returns the matching wine."""
        response = self.client.get(reverse('wine_list'), {'q': 'Wine 1'})
        wines = response.context['wines']

        self.assertEqual(wines.paginator.count, 1)
        self.assertEqual(wines[0].name, 'Wine 1')
        self.assertEqual(response.context['search_query'], 'Wine 1')

    def test_search_by_producer(self):
        """US-08: search by producer returns that producer's wine."""
        response = self.client.get(reverse('wine_list'), {'q': 'Producer 2'})
        wines = response.context['wines']

        self.assertEqual(wines.paginator.count, 1)
        self.assertEqual(wines[0].producer, 'Producer 2')

    def test_search_by_country(self):
        """US-08: search by country returns that country's wines."""
        response = self.client.get(reverse('wine_list'), {'q': 'Spain'})
        wines = response.context['wines']

        self.assertEqual(wines.paginator.count, 1)
        self.assertEqual(wines[0].region.country, 'Spain')

    def test_search_empty_query(self):
        """US-08: empty search returns all wines."""
        response = self.client.get(reverse('wine_list'), {'q': ''})
        self.assertEqual(response.context['wines'].paginator.count, 4)

    def test_search_no_results(self):
        """US-08: search with no matches shows a friendly message."""
        response = self.client.get(reverse('wine_list'), {'q': 'NonexistentWine'})
        wines = response.context['wines']

        self.assertEqual(wines.paginator.count, 0)
        self.assertEqual(response.context['search_query'], 'NonexistentWine')
        self.assertContains(response, 'No wines found for')

    def test_search_stacks_with_type_filter(self):
        """US-08: search combines with the type filter."""
        response = self.client.get(reverse('wine_list'), {
            'q': 'Producer 1',
            'type': 'red'
        })
        wines = response.context['wines']

        self.assertEqual(wines.paginator.count, 1)
        self.assertEqual(wines[0].name, 'Wine 1')
        self.assertEqual(wines[0].wine_type, 'red')
