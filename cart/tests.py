from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from products.models import Wine, Region


class AddToCartTests(TestCase):
    """US-10: Add to cart."""

    def setUp(self):
        self.client = Client()
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
        self.url = reverse("cart_add", args=[self.wine.id])

    def test_add_creates_session_entry(self):
        """US-10: adding a wine stores it in the session cart."""
        response = self.client.post(self.url, {"quantity": 2})
        self.assertRedirects(response, reverse("cart_detail"))
        cart = self.client.session["cart"]
        self.assertEqual(cart[str(self.wine.id)]["quantity"], 2)
        self.assertEqual(cart[str(self.wine.id)]["price"], "25.00")

    def test_adding_same_wine_increases_quantity(self):
        """US-10: adding the same wine again increases its quantity."""
        self.client.post(self.url, {"quantity": 1})
        self.client.post(self.url, {"quantity": 2})
        cart = self.client.session["cart"]
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[str(self.wine.id)]["quantity"], 3)

    def test_quantity_above_stock_is_capped(self):
        """US-10: quantity above stock is capped at stock with a message."""
        response = self.client.post(self.url, {"quantity": 15}, follow=True)
        cart = self.client.session["cart"]
        self.assertEqual(cart[str(self.wine.id)]["quantity"], 10)
        self.assertContains(response, "Only 10 of")

    def test_cannot_exceed_stock_across_adds(self):
        """US-10: repeated adds never take the cart above stock."""
        self.client.post(self.url, {"quantity": 10})
        response = self.client.post(self.url, {"quantity": 1}, follow=True)
        cart = self.client.session["cart"]
        self.assertEqual(cart[str(self.wine.id)]["quantity"], 10)
        self.assertContains(response, "no more")

    def test_unavailable_wine_is_rejected(self):
        """US-10: an unavailable wine cannot be added to the cart."""
        self.wine.is_available = False
        self.wine.save()
        response = self.client.post(self.url, {"quantity": 1}, follow=True)
        self.assertNotIn(str(self.wine.id), self.client.session["cart"])
        self.assertContains(response, "is not available")

    def test_zero_quantity_is_rejected(self):
        """US-10: a quantity of zero is rejected."""
        response = self.client.post(self.url, {"quantity": 0}, follow=True)
        self.assertNotIn(str(self.wine.id), self.client.session["cart"])
        self.assertContains(response, "at least 1")

    def test_negative_quantity_is_rejected(self):
        """US-10: a negative quantity is rejected."""
        response = self.client.post(self.url, {"quantity": -3}, follow=True)
        self.assertNotIn(str(self.wine.id), self.client.session["cart"])
        self.assertContains(response, "at least 1")

    def test_add_requires_post(self):
        """US-10: GET on the add endpoint is not allowed."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class ViewManageCartTests(TestCase):
    """US-11: View and manage the cart."""

    def setUp(self):
        self.client = Client()
        region = Region.objects.create(name="Rioja", country="Spain")
        self.red = Wine.objects.create(
            name="Test Red",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.5,
            price=25.00,
            stock=10,
        )
        self.white = Wine.objects.create(
            name="Test White",
            producer="Test Producer",
            region=region,
            wine_type="white",
            abv=12.0,
            price=15.00,
            stock=10,
        )
        self.client.post(
            reverse("cart_add", args=[self.red.id]), {"quantity": 2}
        )
        self.client.post(
            reverse("cart_add", args=[self.white.id]), {"quantity": 1}
        )

    def test_cart_page_lists_items(self):
        """US-11: cart page shows the wines in the cart."""
        response = self.client.get(reverse("cart_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cart/cart.html")
        self.assertContains(response, "Test Red")
        self.assertContains(response, "Test White")

    def test_cart_total_is_correct(self):
        """US-11: cart total is the sum of price times quantity."""
        response = self.client.get(reverse("cart_detail"))
        cart = response.context["cart"]
        self.assertEqual(cart.get_total_price(), Decimal("65.00"))
        self.assertContains(response, "€65.00")

    def test_remove_updates_session(self):
        """US-11: removing a wine deletes it from the session cart."""
        response = self.client.post(reverse("cart_remove", args=[self.red.id]))
        self.assertRedirects(response, reverse("cart_detail"))
        cart = self.client.session["cart"]
        self.assertNotIn(str(self.red.id), cart)
        self.assertIn(str(self.white.id), cart)

    def test_empty_cart_shows_message(self):
        """US-11: empty cart shows an empty-cart message."""
        self.client.post(reverse("cart_remove", args=[self.red.id]))
        self.client.post(reverse("cart_remove", args=[self.white.id]))
        response = self.client.get(reverse("cart_detail"))
        self.assertContains(response, "Your cart is empty.")
