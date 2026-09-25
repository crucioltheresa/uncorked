from django.test import TestCase, Client
from django.urls import reverse
from .models import Wine, Region
from .utils import COUNTRY_ISO_CODE_MAP, get_countries_with_wine_counts


class ExploreCountriesViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create test regions and wines
        self.france = Region.objects.create(
            name="Burgundy", slug="burgundy", country="France"
        )
        self.spain = Region.objects.create(
            name="Rioja", slug="rioja", country="Spain"
        )
        self.italy = Region.objects.create(
            name="Tuscany", slug="tuscany", country="Italy"
        )
        # Country with no wines
        self.unused = Region.objects.create(
            name="Unknown", slug="unknown", country="Atlantis"
        )

        Wine.objects.create(
            name="Wine 1", slug="wine-1", region=self.france,
            wine_type="red", price=25.0, character="Bold", is_available=True,
            producer="Producer 1", abv=13.5
        )
        Wine.objects.create(
            name="Wine 2", slug="wine-2", region=self.france,
            wine_type="white", price=20.0, character="Crisp", is_available=True,
            producer="Producer 2", abv=12.0
        )
        Wine.objects.create(
            name="Wine 3", slug="wine-3", region=self.spain,
            wine_type="red", price=30.0, character="Fruity", is_available=True,
            producer="Producer 3", abv=14.5
        )
        Wine.objects.create(
            name="Wine 4", slug="wine-4", region=self.italy,
            wine_type="red", price=28.0, character="Complex", is_available=True,
            producer="Producer 4", abv=14.0
        )

    def test_explore_countries_returns_200(self):
        """Test that /countries/ returns 200 status code."""
        response = self.client.get(reverse('explore_countries'))
        self.assertEqual(response.status_code, 200)

    def test_explore_countries_uses_correct_template(self):
        """Test that explore_countries view uses correct template."""
        response = self.client.get(reverse('explore_countries'))
        self.assertTemplateUsed(response, 'products/explore_countries.html')

    def test_only_countries_with_wines_passed_to_template(self):
        """Test that only countries with wines are passed, with correct counts."""
        response = self.client.get(reverse('explore_countries'))
        countries = response.context['countries']

        # Check that we have 3 countries (France, Spain, Italy - not Atlantis)
        self.assertEqual(len(countries), 3)

        # Check counts
        country_dict = {c['name']: c['wine_count'] for c in countries}
        self.assertEqual(country_dict['France'], 2)
        self.assertEqual(country_dict['Spain'], 1)
        self.assertEqual(country_dict['Italy'], 1)

        # Check that Atlantis is not included
        names = [c['name'] for c in countries]
        self.assertNotIn('Atlantis', names)

    def test_country_filter_returns_correct_wines(self):
        """Test that country filter returns the right wines."""
        response = self.client.get(reverse('wine_list'), {'country': 'France'})
        wines = response.context['wines']

        # France has 2 wines
        self.assertEqual(wines.paginator.count, 2)
        names = [w.name for w in wines]
        self.assertIn('Wine 1', names)
        self.assertIn('Wine 2', names)

    def test_country_filter_case_insensitive(self):
        """Test that country filter is case-insensitive."""
        # Test lowercase
        response = self.client.get(reverse('wine_list'), {'country': 'france'})
        wines = response.context['wines']
        self.assertEqual(wines.paginator.count, 2)

        # Test uppercase
        response = self.client.get(reverse('wine_list'), {'country': 'FRANCE'})
        wines = response.context['wines']
        self.assertEqual(wines.paginator.count, 2)

        # Test mixed case
        response = self.client.get(reverse('wine_list'), {'country': 'FrAnCe'})
        wines = response.context['wines']
        self.assertEqual(wines.paginator.count, 2)

    def test_country_filter_stacks_with_type_filter(self):
        """Test that country filter stacks with type filter."""
        # France has 2 wines: 1 red, 1 white
        response = self.client.get(reverse('wine_list'), {
            'country': 'France',
            'type': 'red'
        })
        wines = response.context['wines']

        # Should only get 1 wine (red)
        self.assertEqual(wines.paginator.count, 1)
        self.assertEqual(wines[0].name, 'Wine 1')
        self.assertEqual(wines[0].wine_type, 'red')

    def test_all_countries_in_database_have_iso_mapping(self):
        """Test that every country in database has an ISO mapping."""
        all_wines = Wine.objects.all()
        countries = set()

        for wine in all_wines:
            countries.add(wine.region.country)

        # Check each country has a mapping
        for country in countries:
            self.assertIn(
                country, COUNTRY_ISO_CODE_MAP,
                f"Country '{country}' is in database but missing from ISO mapping"
            )

    def test_get_countries_with_wine_counts(self):
        """Test that get_countries_with_wine_counts returns correct data."""
        countries = get_countries_with_wine_counts()

        # Should have 3 countries
        self.assertEqual(len(countries), 3)

        # Check structure
        for country in countries:
            self.assertIn('name', country)
            self.assertIn('iso_code', country)
            self.assertIn('wine_count', country)

        # Check values
        country_dict = {c['name']: c for c in countries}
        self.assertEqual(country_dict['France']['wine_count'], 2)
        self.assertEqual(country_dict['France']['iso_code'], 'FRA')
        self.assertEqual(country_dict['Spain']['wine_count'], 1)
        self.assertEqual(country_dict['Spain']['iso_code'], 'ESP')
