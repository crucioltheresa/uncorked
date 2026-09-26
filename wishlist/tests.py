from django.test import TestCase, Client
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
            WishlistItem.objects.filter(user=self.user, wine=self.wine).exists()
        )

    def test_duplicate_shows_info_message(self):
        """US-16: adding the same wine twice shows an info message."""
        self.client.login(username="test@example.com", password="testpass123")
        self.client.post(self.url)
        response = self.client.post(self.url, follow=True)
        self.assertEqual(WishlistItem.objects.filter(user=self.user).count(), 1)
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
