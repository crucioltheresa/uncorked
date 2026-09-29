from django.db import connection
from django.test import TestCase, Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Wine, Region
from .models import WishlistItem

User = get_user_model()


class AddToWishlistTests(TestCase):
    """US-16: Add to wishlist."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Test Red",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.5,
            price=25.00,
            stock=10,
        )
        self.url = reverse("wishlist_add", args=[self.wine.id])

    def test_add_with_get_returns_405(self):
        """US-16: adding to the wishlist with GET is not allowed."""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertFalse(WishlistItem.objects.exists())

    def test_add_requires_login(self):
        """US-16: anonymous users are redirected to login."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login"))
        self.assertFalse(WishlistItem.objects.exists())

    def test_add_creates_item(self):
        """US-16: adding a wine creates a wishlist item."""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.post(self.url)
        self.assertRedirects(
            response, reverse("wine_detail", args=[self.wine.slug])
        )
        self.assertTrue(
            WishlistItem.objects.filter(
                user=self.user, wine=self.wine
            ).exists()
        )

    def test_duplicate_shows_info_message(self):
        """US-16: adding the same wine twice shows an info message."""
        self.client.login(username="test@example.com", password="testpass123")
        self.client.post(self.url)
        response = self.client.post(self.url, follow=True)
        self.assertEqual(
            WishlistItem.objects.filter(user=self.user).count(), 1
        )
        self.assertContains(response, "is already in your wishlist")


class ViewManageWishlistTests(TestCase):
    """US-17: View and manage the wishlist."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            username="otheruser",
            password="testpass123",
        )
        region = Region.objects.create(name="Rioja", country="Spain")
        self.my_wine = Wine.objects.create(
            name="My Red",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.5,
            price=25.00,
            stock=10,
        )
        self.their_wine = Wine.objects.create(
            name="Their White",
            producer="Test Producer",
            region=region,
            wine_type="white",
            abv=12.0,
            price=15.00,
            stock=10,
        )
        WishlistItem.objects.create(user=self.user, wine=self.my_wine)
        WishlistItem.objects.create(user=self.other_user, wine=self.their_wine)
        self.client.login(username="test@example.com", password="testpass123")

    def test_remove_with_get_returns_405(self):
        """US-17: removing from the wishlist with GET is not allowed."""
        response = self.client.get(
            reverse("wishlist_remove", args=[self.my_wine.id])
        )
        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            WishlistItem.objects.filter(
                user=self.user, wine=self.my_wine
            ).exists()
        )

    def test_wishlist_requires_login(self):
        """US-17: anonymous users are redirected to login."""
        self.client.logout()
        response = self.client.get(reverse("wishlist_detail"))
        self.assertEqual(response.status_code, 302)

    def test_wishlist_shows_only_own_items(self):
        """US-17: wishlist lists only the user's own wines."""
        response = self.client.get(reverse("wishlist_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wishlist/wishlist.html")
        self.assertContains(response, "My Red")
        self.assertNotContains(response, "Their White")

    def test_remove_deletes_item(self):
        """US-17: removing a wine deletes it from the wishlist."""
        response = self.client.post(
            reverse("wishlist_remove", args=[self.my_wine.id])
        )
        self.assertRedirects(response, reverse("wishlist_detail"))
        self.assertFalse(
            WishlistItem.objects.filter(
                user=self.user, wine=self.my_wine
            ).exists()
        )

    def test_remove_does_not_touch_other_users_items(self):
        """US-17: removing a wine never deletes another user's item."""
        self.client.post(reverse("wishlist_remove", args=[self.their_wine.id]))
        self.assertTrue(
            WishlistItem.objects.filter(
                user=self.other_user, wine=self.their_wine
            ).exists()
        )


class FavouriteStarTests(TestCase):
    """US-16 / US-17: Favourite star on wine cards."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="star@example.com",
            username="staruser",
            password="testpass123",
        )
        region = Region.objects.create(name="Rioja", country="Spain")
        self.liked = Wine.objects.create(
            name="Liked Red", producer="Test", region=region,
            wine_type="red", abv=13.5, price="20.00", stock=5,
            is_featured=True,
        )
        self.other = Wine.objects.create(
            name="Other White", producer="Test", region=region,
            wine_type="white", abv=12.0, price="15.00", stock=5,
        )
        WishlistItem.objects.create(user=self.user, wine=self.liked)
        self.toggle_url = reverse("wishlist_toggle", args=[self.other.id])

    def test_catalogue_shows_filled_and_outline_stars(self):
        """US-16: favourites get a filled, pressed star; others don't."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("wine_list"))
        self.assertContains(
            response,
            'aria-pressed="true" '
            'aria-label="Remove Liked Red from favourites"',
        )
        self.assertContains(
            response,
            'aria-pressed="false" aria-label="Add Other White to favourites"',
        )
        self.assertContains(
            response, "favourite-star__button--active", count=1
        )
        self.assertContains(response, "bi bi-star-fill", count=1)

    def test_homepage_new_arrivals_show_stars(self):
        """US-16: the homepage new arrivals cards have the star too."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("homepage"))
        self.assertContains(response, "Remove Liked Red from favourites")

    def test_toggle_adds_then_removes(self):
        """US-16 / US-17: the star adds the wine, then removes it."""
        self.client.force_login(self.user)
        next_url = reverse("wine_list") + "?type=white"
        response = self.client.post(self.toggle_url, {"next": next_url})
        self.assertRedirects(response, next_url)
        self.assertTrue(
            WishlistItem.objects.filter(
                user=self.user, wine=self.other
            ).exists()
        )
        self.client.post(self.toggle_url, {"next": next_url})
        self.assertFalse(
            WishlistItem.objects.filter(
                user=self.user, wine=self.other
            ).exists()
        )

    def test_toggle_returns_json_for_fetch(self):
        """US-16: fetch requests get JSON with the new state and a message."""
        self.client.force_login(self.user)
        response = self.client.post(
            self.toggle_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertTrue(data["in_wishlist"])
        self.assertEqual(data["wine_id"], self.other.id)
        self.assertEqual(data["count"], 2)
        self.assertIn("added to your favourites", data["message"])

        data = self.client.post(
            self.toggle_url, HTTP_ACCEPT="application/json"
        ).json()
        self.assertFalse(data["in_wishlist"])
        self.assertEqual(data["count"], 1)

    def test_toggle_requires_post_and_login(self):
        """US-16: GET is not allowed and anonymous users go to login."""
        response = self.client.post(self.toggle_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.toggle_url).status_code, 405)

    def test_toggle_ignores_external_next_url(self):
        """US-16: the form never redirects to another site."""
        self.client.force_login(self.user)
        response = self.client.post(
            self.toggle_url, {"next": "https://evil.example/steal"}
        )
        self.assertRedirects(
            response, reverse("wine_list"), fetch_redirect_response=False
        )

    def test_logged_out_star_links_to_login(self):
        """US-16: logged out, the star links to login and back to the page."""
        response = self.client.get(reverse("wine_list") + "?type=red")
        self.assertContains(
            response,
            'href="/accounts/login/?next=/wines/%3Ftype%3Dred"',
        )
        self.assertNotContains(response, "data-favourite-form")

    def test_wishlist_ids_loaded_in_one_query(self):
        """US-16: one wishlist query per page, however many cards."""
        region = Region.objects.first()
        for i in range(6):
            Wine.objects.create(
                name=f"Extra {i}", producer="Test", region=region,
                wine_type="red", abv=13, price="10.00", stock=5,
            )
        self.client.force_login(self.user)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("wine_list"))
        self.assertEqual(response.status_code, 200)
        wishlist_queries = [
            q for q in queries.captured_queries
            if "wishlist_wishlistitem" in q["sql"]
        ]
        self.assertEqual(len(wishlist_queries), 1)


class FavouritesPageTests(TestCase):
    """US-17: The favourites page: quantity, add to cart and remove."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="fav@example.com", username="favuser", password="x"
        )
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Fav Red", producer="Test", region=region,
            wine_type="red", abv=13.5, price="12.00", stock=6,
        )
        self.gone = Wine.objects.create(
            name="Gone White", producer="Test", region=region,
            wine_type="white", abv=12.0, price="10.00", stock=5,
            is_available=False,
        )
        self.empty = Wine.objects.create(
            name="Sold Out Rose", producer="Test", region=region,
            wine_type="rose", abv=12.0, price="10.00", stock=0,
        )
        for wine in [self.wine, self.gone, self.empty]:
            WishlistItem.objects.create(user=self.user, wine=wine)
        self.client.force_login(self.user)

    def test_page_shows_stepper_add_and_remove(self):
        """US-17: each favourite has a stepper, add to cart and remove."""
        response = self.client.get(reverse("wishlist_detail"))
        self.assertContains(
            response,
            '<input type="number" name="quantity" value="1" min="1" max="6" '
            'aria-label="Quantity of Fav Red">',
            html=True,
        )
        self.assertContains(
            response, f'action="{reverse("cart_add", args=[self.wine.id])}"'
        )
        self.assertContains(
            response,
            f'action="{reverse("wishlist_remove", args=[self.wine.id])}"',
        )
        self.assertContains(response, "Remove from favourites", count=3)

    def test_add_to_cart_uses_chosen_quantity(self):
        """US-17: adding from favourites adds the quantity chosen."""
        self.client.post(
            reverse("cart_add", args=[self.wine.id]), {"quantity": 4}
        )
        cart = self.client.session["cart"]
        self.assertEqual(cart[str(self.wine.id)]["quantity"], 4)

    def test_unavailable_and_out_of_stock_disable_add_to_cart(self):
        """US-17: unavailable or out-of-stock wines can't be added."""
        response = self.client.get(reverse("wishlist_detail"))
        self.assertContains(response, "No longer available")
        self.assertContains(response, "Out of stock")
        self.assertContains(
            response,
            '<button type="submit" class="wine-card__add-btn" disabled '
            'aria-disabled="true">Add to Cart</button>',
            count=2,
            html=True,
        )

    def test_remove_from_favourites(self):
        """US-17: removing takes the wine out of the favourites."""
        response = self.client.post(
            reverse("wishlist_remove", args=[self.wine.id])
        )
        self.assertRedirects(response, reverse("wishlist_detail"))
        self.assertFalse(
            WishlistItem.objects.filter(
                user=self.user, wine=self.wine
            ).exists()
        )

    def test_remove_returns_json_for_fetch_and_never_re_adds(self):
        """US-17: remove answers fetch with JSON and is safe to repeat."""
        url = reverse("wishlist_remove", args=[self.wine.id])
        for _ in range(2):
            data = self.client.post(
                url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
            ).json()
            self.assertFalse(data["in_wishlist"])
        self.assertEqual(data["count"], 2)
        self.assertFalse(
            WishlistItem.objects.filter(
                user=self.user, wine=self.wine
            ).exists()
        )

    def test_empty_state_when_no_favourites(self):
        """US-17: with no favourites, the empty message shows."""
        WishlistItem.objects.filter(user=self.user).delete()
        response = self.client.get(reverse("wishlist_detail"))
        self.assertContains(response, "saved any favourites yet.")
        self.assertNotContains(response, "data-favourite-card")


class WineDetailFavouriteButtonTests(TestCase):
    """US-16: The wine page's add / remove favourites button."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="detail@example.com", username="detailuser", password="x"
        )
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Detail Red", producer="Test", region=region,
            wine_type="red", abv=13.5, price="12.00", stock=6,
        )
        self.url = reverse("wine_detail", args=[self.wine.slug])
        self.client.force_login(self.user)

    def test_shows_add_when_not_a_favourite(self):
        """US-16: not a favourite: star icon and "Add to favourites"."""
        response = self.client.get(self.url)
        self.assertContains(
            response,
            'aria-pressed="false" aria-label="Add Detail Red to favourites"',
        )
        self.assertContains(
            response,
            "<span data-favourite-text>Add to favourites</span>",
            html=True,
        )
        self.assertContains(
            response,
            f'formaction="{reverse("wishlist_toggle", args=[self.wine.id])}"',
        )

    def test_shows_remove_when_a_favourite(self):
        """US-16: a favourite: X icon and "Remove from favourites"."""
        WishlistItem.objects.create(user=self.user, wine=self.wine)
        response = self.client.get(self.url)
        self.assertContains(
            response,
            'aria-pressed="true" '
            'aria-label="Remove Detail Red from favourites"',
        )
        self.assertContains(
            response, '<i class="bi bi-x-lg" aria-hidden="true"></i>',
            html=True,
        )
        self.assertContains(
            response,
            "<span data-favourite-text>Remove from favourites</span>",
            html=True,
        )

    def test_toggling_switches_the_button(self):
        """US-16: the button adds, then removes, returning to the page."""
        toggle = reverse("wishlist_toggle", args=[self.wine.id])
        page = f"http://testserver{self.url}"
        response = self.client.post(
            toggle, {"quantity": 1}, HTTP_REFERER=page
        )
        self.assertRedirects(response, page, fetch_redirect_response=False)
        self.assertContains(
            self.client.get(self.url), "Remove from favourites"
        )
        self.client.post(toggle, {"quantity": 1})
        self.assertContains(self.client.get(self.url), "Add to favourites")
