from unittest.mock import patch

import cloudinary
from cloudinary.exceptions import NotFound
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from orders.models import Order, OrderItem
from uncorked.storages import CloudinaryMediaStorage
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


class CatalogueTests(TestCase):
    """US-05: Browse the catalogue."""

    def setUp(self):
        self.client = Client()
        create_test_wines()
        Wine.objects.filter(name="Wine 4").update(is_available=False)

    def test_catalogue_loads(self):
        """US-05: catalogue returns 200 with the wine list template."""
        response = self.client.get(reverse('wine_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/wine_list.html')

    def test_unavailable_wine_not_in_catalogue(self):
        """US-05: unavailable wines are not listed in the catalogue."""
        response = self.client.get(reverse('wine_list'))
        self.assertEqual(response.context['wines'].paginator.count, 3)
        self.assertNotContains(response, 'Wine 4')


class FilterByTypeTests(TestCase):
    """US-06: Filter the catalogue by wine type."""

    def setUp(self):
        self.client = Client()
        create_test_wines()

    def test_type_filter_returns_only_that_type(self):
        """US-06: ?type=red returns only red wines."""
        response = self.client.get(reverse('wine_list'), {'type': 'red'})
        wines = response.context['wines']
        self.assertEqual(wines.paginator.count, 3)
        for wine in wines:
            self.assertEqual(wine.wine_type, 'red')

    def test_invalid_type_returns_all_wines(self):
        """US-06: an unknown ?type= value shows all wines."""
        response = self.client.get(reverse('wine_list'), {'type': 'beer'})
        self.assertEqual(response.context['wines'].paginator.count, 4)
        self.assertIsNone(response.context['selected_type'])


class WineDetailTests(TestCase):
    """US-07: Wine detail page."""

    def setUp(self):
        self.client = Client()
        create_test_wines()

    def test_wine_detail_loads(self):
        """US-07: wine detail returns 200 with the wine's details."""
        response = self.client.get(reverse('wine_detail', args=['wine-1']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/wine_detail.html')
        self.assertContains(response, 'Wine 1')

    def test_unavailable_wine_returns_404(self):
        """US-07: unavailable wine detail returns 404."""
        Wine.objects.filter(slug='wine-1').update(is_available=False)
        response = self.client.get(reverse('wine_detail', args=['wine-1']))
        self.assertEqual(response.status_code, 404)


class RelatedWinesTests(TestCase):
    """US-07: "You may also like" on the wine detail page."""

    def setUp(self):
        self.client = Client()
        region = Region.objects.create(name="Rioja", country="Spain")

        def wine(name, wine_type="red", **fields):
            return Wine.objects.create(
                name=name, producer="Test", region=region,
                wine_type=wine_type, abv=13, price="15.00", stock=5,
                **fields,
            )

        self.current = wine("Current Red")
        # Five other available reds: more than the four shown
        self.other_reds = [wine(f"Other Red {i}") for i in range(5)]
        self.hidden_red = wine("Hidden Red", is_available=False)
        self.white = wine("Some White", wine_type="white")
        self.url = reverse("wine_detail", args=[self.current.slug])

    def related(self):
        return list(self.client.get(self.url).context["related_wines"])

    def test_shows_up_to_four_wines(self):
        """US-07: the section shows at most four wines."""
        response = self.client.get(self.url)
        self.assertContains(response, "YOU MAY ALSO LIKE")
        self.assertEqual(len(response.context["related_wines"]), 4)

    def test_only_other_available_wines_of_the_same_type(self):
        """US-07: same type only; never the current or unavailable wine."""
        related = self.related()
        self.assertNotIn(self.current, related)
        self.assertNotIn(self.hidden_red, related)
        self.assertNotIn(self.white, related)
        for wine in related:
            self.assertEqual(wine.wine_type, "red")
            self.assertTrue(wine.is_available)
            self.assertIn(wine, self.other_reds)

    def test_cards_link_to_the_related_wines(self):
        """US-07: each related card links to its wine, not the current."""
        response = self.client.get(self.url)
        for wine in response.context["related_wines"]:
            self.assertContains(
                response, reverse("wine_detail", args=[wine.slug])
            )
        self.assertNotContains(response, "Hidden Red")
        self.assertNotContains(response, "Some White")

    def test_section_hidden_when_nothing_matches(self):
        """US-07: no other wine of the same type, no section."""
        response = self.client.get(
            reverse("wine_detail", args=[self.white.slug])
        )
        self.assertEqual(list(response.context["related_wines"]), [])
        self.assertNotContains(response, "YOU MAY ALSO LIKE")


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
        """US-29: only countries with wines are listed, A-Z, with counts."""
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
            response = self.client.get(
                reverse('wine_list'), {'country': value}
            )
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


class CountryLinkEncodingTests(TestCase):
    """US-29: Country links are URL-encoded (names with spaces)."""

    COUNTRIES = ['Czech Republic', 'New Zealand', 'South Africa']

    def setUp(self):
        self.client = Client()
        for number, country in enumerate(self.COUNTRIES):
            region = Region.objects.create(
                name=f'Region {number}', slug=f'region-{number}',
                country=country,
            )
            Wine.objects.create(
                name=f'{country} Wine', slug=f'country-wine-{number}',
                region=region, wine_type='red', price=20.0,
                producer='Producer', abv=13.0, is_available=True,
            )

    def test_nav_country_links_are_encoded(self):
        """US-29: nav country links use %20, never a raw space."""
        response = self.client.get(reverse('homepage'))
        for country in self.COUNTRIES:
            encoded = country.replace(' ', '%20')
            # Desktop dropdown and mobile accordion
            self.assertContains(
                response, f'href="/wines/?country={encoded}"', count=2
            )
            self.assertNotContains(response, f'?country={country}"')

    def test_map_gets_catalogue_url_for_encoded_links(self):
        """US-29: the map builds its links from a plain catalogue URL."""
        response = self.client.get(reverse('homepage'))
        self.assertContains(
            response,
            f'class="world-map-container" '
            f'data-wine-list-url="{reverse("wine_list")}"',
        )

    def test_encoded_country_links_filter_the_catalogue(self):
        """US-29: following an encoded country link shows that country."""
        for country in self.COUNTRIES:
            encoded = country.replace(' ', '%20')
            response = self.client.get(f'/wines/?country={encoded}')
            wines = response.context['wines']
            self.assertEqual(wines.paginator.count, 1)
            self.assertEqual(wines[0].name, f'{country} Wine')

    def test_pagination_links_are_encoded(self):
        """US-29: page links keep the country and search, encoded."""
        region = Region.objects.get(country='South Africa')
        for number in range(12):
            Wine.objects.create(
                name=f'Extra {number}', slug=f'extra-{number}',
                region=region, wine_type='red', price=20.0,
                producer='Producer', abv=13.0, is_available=True,
            )
        response = self.client.get(
            reverse('wine_list'),
            {'country': 'South Africa', 'q': 'South Africa'},
        )
        self.assertEqual(response.context['wines'].paginator.num_pages, 2)
        self.assertContains(response, '&amp;country=South%20Africa')
        self.assertContains(response, '&amp;q=South%20Africa')
        self.assertNotContains(response, 'country=South Africa')


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
        response = self.client.get(
            reverse('wine_list'), {'q': 'NonexistentWine'}
        )
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


TINY_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
    b"!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
    b"\x00\x00\x02\x02D\x01\x00;"
)
CLOUDINARY_STORAGES = {
    "default": {"BACKEND": "uncorked.storages.CloudinaryMediaStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


@override_settings(STORAGES=CLOUDINARY_STORAGES)
@patch.object(cloudinary.config(), "cloud_name", "uncorked-test")
@patch("uncorked.storages.cloudinary.api.resource", side_effect=NotFound)
@patch("uncorked.storages.cloudinary.uploader.upload")
class WineImageUploadTests(TestCase):
    """US-09: Wine images uploaded in the admin go to Cloudinary."""

    def setUp(self):
        self.client = Client()
        admin = get_user_model().objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass123",
        )
        self.client.force_login(admin)

    def test_admin_image_upload_goes_to_cloudinary(self, mock_upload, _):
        """US-09: admin image upload is sent to Cloudinary, name unchanged."""
        response = self.client.post(reverse("admin:products_wine_add"), {
            "name": "Uploaded Wine",
            "producer": "Test Producer",
            "wine_type": "red",
            "abv": "13.5",
            "price": "20.00",
            "stock": "5",
            "slug": "uploaded-wine",
            "is_available": "on",
            "image": SimpleUploadedFile(
                "label.gif", TINY_GIF, content_type="image/gif"
            ),
        })
        self.assertEqual(response.status_code, 302)
        wine = Wine.objects.get(slug="uploaded-wine")
        self.assertEqual(wine.image.name, "wines/label.gif")
        kwargs = mock_upload.call_args.kwargs
        self.assertEqual(kwargs["public_id"], "media/wines/label")
        self.assertEqual(kwargs["resource_type"], "image")

    def test_image_url_points_to_cloudinary(self, mock_upload, _):
        """US-09: stored image names are served from Cloudinary."""
        url = CloudinaryMediaStorage().url("wines/image_3.jpg")
        self.assertTrue(
            url.startswith("https://res.cloudinary.com/uncorked-test/")
        )
        self.assertTrue(url.endswith("/media/wines/image_3.jpg"))
        mock_upload.assert_not_called()


class ProductManagementTests(TestCase):
    """US-09: Superusers manage the catalogue from the front end."""

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass123",
        )
        self.customer = User.objects.create_user(
            email="customer@example.com",
            username="customer",
            password="testpass123",
        )
        self.region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Plain Red",
            producer="Test Producer",
            region=self.region,
            wine_type="red",
            abv=13.5,
            price=20.00,
            stock=10,
        )
        self.ordered_wine = Wine.objects.create(
            name="Ordered Red",
            producer="Test Producer",
            region=self.region,
            wine_type="red",
            abv=13.5,
            price=25.00,
            stock=10,
        )
        order = Order.objects.create(
            full_name="Customer",
            email="customer@example.com",
            address_line1="1 Main St",
            city="Madrid",
            postcode="28001",
            country="Spain",
            grand_total=25.00,
            status="paid",
        )
        OrderItem.objects.create(
            order=order,
            wine=self.ordered_wine,
            quantity=1,
            price_at_purchase=25.00,
        )
        self.add_url = reverse("wine_add")
        self.edit_url = reverse("wine_edit", args=[self.wine.slug])
        self.delete_url = reverse("wine_delete", args=[self.wine.slug])
        self.form_data = {
            "name": "New Rioja",
            "producer": "Bodega Test",
            "region": self.region.id,
            "wine_type": "red",
            "vintage": 2020,
            "abv": "14.0",
            "price": "29.50",
            "stock": 12,
            "character": "Bold",
            "tasting_notes": "Cherry and spice.",
            "food_pairing": "Lamb",
            "description": "Family estate.",
            "is_available": "on",
        }

    def test_logged_out_user_redirected_to_login(self):
        """US-09: logged-out users are sent to login from every page."""
        for url in [self.add_url, self.edit_url, self.delete_url]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_non_superuser_cannot_add_wine(self):
        """US-09: a customer can't add a wine and sees an error message."""
        self.client.force_login(self.customer)
        response = self.client.post(
            self.add_url, self.form_data, follow=True
        )
        self.assertRedirects(response, reverse("wine_list"))
        self.assertContains(response, "Only site administrators")
        self.assertFalse(Wine.objects.filter(name="New Rioja").exists())

    def test_non_superuser_cannot_edit_wine(self):
        """US-09: a customer can't edit a wine."""
        self.client.force_login(self.customer)
        data = dict(self.form_data, name="Hacked")
        response = self.client.post(self.edit_url, data)
        self.assertRedirects(
            response, reverse("wine_list"), fetch_redirect_response=False
        )
        self.wine.refresh_from_db()
        self.assertEqual(self.wine.name, "Plain Red")

    def test_non_superuser_cannot_delete_wine(self):
        """US-09: a customer can't delete a wine."""
        self.client.force_login(self.customer)
        response = self.client.post(self.delete_url)
        self.assertRedirects(
            response, reverse("wine_list"), fetch_redirect_response=False
        )
        self.assertTrue(Wine.objects.filter(pk=self.wine.pk).exists())

    def test_superuser_can_add_wine_with_image(self):
        """US-09: a superuser adds a wine with an image and sees it."""
        self.client.force_login(self.admin)
        data = dict(
            self.form_data,
            image=SimpleUploadedFile(
                "rioja.gif", TINY_GIF, content_type="image/gif"
            ),
        )
        response = self.client.post(self.add_url, data, follow=True)
        wine = Wine.objects.get(name="New Rioja")
        self.assertRedirects(
            response, reverse("wine_detail", args=[wine.slug])
        )
        self.assertContains(response, "New Rioja&quot; was added.")
        self.assertEqual(wine.region, self.region)
        self.assertEqual(wine.image.name, "wines/rioja.gif")
        self.assertTrue(default_storage.exists("wines/rioja.gif"))

    def test_add_with_invalid_data_shows_errors(self):
        """US-09: invalid data is not saved and errors are shown."""
        self.client.force_login(self.admin)
        data = dict(self.form_data, price="-5", name="")
        response = self.client.post(self.add_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/wine_form.html")
        self.assertContains(response, "Price must be more than 0.")
        self.assertContains(response, "Please correct the errors below.")
        self.assertEqual(Wine.objects.count(), 2)

    def test_add_duplicate_name_and_vintage_shows_error(self):
        """US-09: a wine with the same name and vintage is rejected."""
        self.client.force_login(self.admin)
        data = dict(self.form_data, name="Plain Red", vintage="")
        response = self.client.post(self.add_url, data)
        self.assertContains(
            response, "A wine with this name and vintage already exists."
        )
        self.assertEqual(Wine.objects.filter(name="Plain Red").count(), 1)

    def test_edit_page_is_prefilled(self):
        """US-09: the edit page shows the wine's current values."""
        self.client.force_login(self.admin)
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].instance, self.wine)
        self.assertContains(response, 'value="Plain Red"')

    def test_edit_page_shows_current_image(self):
        """US-09: the edit page shows the current image and a replace field."""
        self.wine.image.save(
            "current.gif", SimpleUploadedFile("current.gif", TINY_GIF)
        )
        self.client.force_login(self.admin)
        response = self.client.get(self.edit_url)
        self.assertContains(response, "Current image of Plain Red")
        self.assertContains(response, "Replace image")

    def test_superuser_can_edit_wine(self):
        """US-09: a superuser edits a wine and returns to its detail page."""
        self.client.force_login(self.admin)
        data = dict(self.form_data, name="Plain Red", price="22.00")
        response = self.client.post(self.edit_url, data, follow=True)
        self.assertRedirects(
            response, reverse("wine_detail", args=[self.wine.slug])
        )
        self.assertContains(response, "Plain Red&quot; was updated.")
        self.wine.refresh_from_db()
        self.assertEqual(str(self.wine.price), "22.00")

    def test_delete_requires_post(self):
        """US-09: GET shows a confirmation page and deletes nothing."""
        self.client.force_login(self.admin)
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/wine_confirm_delete.html")
        self.assertContains(
            response, "Are you sure you want to delete <strong>Plain Red"
        )
        self.assertTrue(Wine.objects.filter(pk=self.wine.pk).exists())

    def test_superuser_can_delete_wine_without_orders(self):
        """US-09: a wine with no orders is deleted."""
        self.client.force_login(self.admin)
        response = self.client.post(self.delete_url, follow=True)
        self.assertRedirects(response, reverse("wine_list"))
        self.assertContains(response, "Plain Red&quot; was deleted.")
        self.assertFalse(Wine.objects.filter(pk=self.wine.pk).exists())

    def test_wine_with_orders_is_marked_unavailable(self):
        """US-09: a wine in existing orders is kept but made unavailable."""
        self.client.force_login(self.admin)
        url = reverse("wine_delete", args=[self.ordered_wine.slug])
        response = self.client.post(url, follow=True)
        self.ordered_wine.refresh_from_db()
        self.assertFalse(self.ordered_wine.is_available)
        self.assertContains(response, "marked unavailable instead")
        self.assertContains(response, "hidden from customers")

    def test_admin_links_shown_only_to_superusers(self):
        """US-09: edit, delete and add links appear only for superusers."""
        detail_url = reverse("wine_detail", args=[self.wine.slug])
        list_url = reverse("wine_list")
        profile_url = reverse("profile")
        self.client.force_login(self.customer)
        self.assertNotContains(self.client.get(detail_url), self.edit_url)
        self.assertNotContains(self.client.get(list_url), self.edit_url)
        self.assertNotContains(self.client.get(profile_url), self.add_url)

        self.client.force_login(self.admin)
        self.assertContains(self.client.get(detail_url), self.delete_url)
        self.assertContains(self.client.get(list_url), self.edit_url)
        self.assertContains(self.client.get(profile_url), self.add_url)

    def test_uploads_use_in_memory_storage_in_tests(self):
        """US-09: tests never upload to Cloudinary."""
        self.assertEqual(
            default_storage.__class__.__name__, "InMemoryStorage"
        )


class RegionDisplayTests(TestCase):
    """US-05 / US-29: A region equal to its country is shown once."""

    def test_region_and_country_shown_together(self):
        """US-29: a normal region reads "Rioja, Spain"."""
        region = Region(name="Rioja", country="Spain")
        self.assertEqual(str(region), "Rioja, Spain")

    def test_same_name_shown_once(self):
        """US-29: "Spain, Spain" becomes "Spain" (any case or spacing)."""
        self.assertEqual(str(Region(name="Spain", country="Spain")), "Spain")
        self.assertEqual(
            str(Region(name=" spain ", country="Spain")), "Spain"
        )

    def test_catalogue_and_dashboard_show_it_once(self):
        """US-05: the catalogue and dashboard never say "Spain, Spain"."""
        region = Region.objects.create(name="Spain", country="Spain")
        Wine.objects.create(
            name="Country Red", producer="Test", region=region,
            wine_type="red", abv=13, price="10.00", stock=5,
        )
        admin = get_user_model().objects.create_superuser(
            email="dev@example.com", username="dev", password="x"
        )
        self.client.force_login(admin)
        for url in [reverse("wine_list"), reverse("dashboard:wines")]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "Spain")
                self.assertNotContains(response, "Spain, Spain")
