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


class CartPageLayoutTests(TestCase):
    """US-11: Cart rows show a thumbnail; the summary shows the totals."""

    def setUp(self):
        self.client = Client()
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Test Red",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.5,
            price="12.50",
            stock=20,
            image="wines/image_1.jpg",
        )

    def add(self, quantity):
        self.client.post(
            reverse("cart_add", args=[self.wine.id]), {"quantity": quantity}
        )

    def test_cart_row_shows_thumbnail(self):
        """US-11: each cart row shows the wine's thumbnail."""
        self.add(1)
        response = self.client.get(reverse("cart_detail"))
        self.assertContains(response, 'class="cart__thumb"')
        self.assertContains(response, self.wine.image.url)

    def test_cart_totals_without_discount(self):
        """US-11: under 8 bottles: subtotal, no discount, delivery later."""
        self.add(2)
        response = self.client.get(reverse("cart_detail"))
        totals = response.context["totals"]
        self.assertEqual(totals.subtotal, Decimal("25.00"))
        self.assertEqual(totals.grand_total, Decimal("25.00"))
        self.assertContains(response, "Subtotal")
        self.assertNotContains(response, "totals__row--discount")
        self.assertContains(response, "Calculated at checkout")
        self.assertContains(response, "Continue Shopping")
        self.assertContains(response, "Proceed to Checkout")

    def test_cart_totals_with_discount_and_free_delivery(self):
        """US-11: 9 bottles of €12.50 get 10% off and free delivery."""
        self.add(9)
        response = self.client.get(reverse("cart_detail"))
        totals = response.context["totals"]
        self.assertEqual(totals.subtotal, Decimal("112.50"))
        self.assertEqual(totals.discount, Decimal("11.25"))
        self.assertEqual(totals.grand_total, Decimal("101.25"))
        self.assertContains(response, "−€11.25")
        self.assertContains(response, "Free")
        self.assertContains(response, "€101.25")


class CartBadgeTests(TestCase):
    """US-11: The nav cart badge counts bottles, not different wines."""

    def setUp(self):
        self.client = Client()
        region = Region.objects.create(name="Rioja", country="Spain")
        self.red = Wine.objects.create(
            name="Badge Red", producer="Test", region=region,
            wine_type="red", abv=13.5, price="10.00", stock=20,
        )
        self.white = Wine.objects.create(
            name="Badge White", producer="Test", region=region,
            wine_type="white", abv=12.0, price="10.00", stock=20,
        )

    def test_badge_shows_total_bottles(self):
        """US-11: 3 reds and 2 whites show 5 on the badge."""
        self.client.post(
            reverse("cart_add", args=[self.red.id]), {"quantity": 3}
        )
        self.client.post(
            reverse("cart_add", args=[self.white.id]), {"quantity": 2}
        )
        response = self.client.get(reverse("wine_list"))
        self.assertEqual(response.context["cart_bottle_count"], 5)
        self.assertContains(
            response,
            '<span class="nav__icon-count" aria-hidden="true">5</span>',
            html=True,
        )

    def test_cart_link_name_includes_bottle_count(self):
        """US-11: the cart link names the count; the badge has no label."""
        self.client.post(
            reverse("cart_add", args=[self.red.id]), {"quantity": 3}
        )
        response = self.client.get(reverse("wine_list"))
        self.assertContains(
            response,
            '<span class="visually-hidden" data-cart-link-text>'
            "Your cart, 3 bottles</span>",
            html=True,
        )
        self.assertNotContains(response, "in your cart")

    def test_no_badge_when_cart_is_empty(self):
        """US-11: an empty cart shows no badge and creates no cart."""
        response = self.client.get(reverse("wine_list"))
        self.assertEqual(response.context["cart_bottle_count"], 0)
        self.assertNotContains(response, "nav__icon-count")
        self.assertContains(response, ">Your cart</span>")
        self.assertNotIn("cart", self.client.session)


class CartPreviewTests(TestCase):
    """US-11: The nav cart preview endpoint."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("cart_preview")
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wines = [
            Wine.objects.create(
                name=f"Preview Wine {i}", producer="Test", region=region,
                wine_type="red", abv=13, price="10.00", stock=20,
            )
            for i in range(6)
        ]

    def add(self, client, wine, quantity):
        client.post(
            reverse("cart_add", args=[wine.id]), {"quantity": quantity}
        )

    def test_empty_state(self):
        """US-11: an empty cart shows the empty message and catalogue link."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your cart is empty.")
        self.assertContains(response, reverse("wine_list"))
        self.assertNotIn("cart", self.client.session)

    def test_items_and_subtotal(self):
        """US-11: items show with quantity and line total, plus subtotal."""
        self.add(self.client, self.wines[0], 2)
        self.add(self.client, self.wines[1], 1)
        response = self.client.get(self.url)
        self.assertContains(response, "Preview Wine 0")
        self.assertContains(response, "Qty 2")
        self.assertContains(response, "€20.00")
        self.assertEqual(response.context["totals"].subtotal, Decimal("30.00"))
        self.assertContains(response, reverse("cart_detail"))
        self.assertContains(response, reverse("checkout"))
        self.assertNotContains(response, "Discount")

    def test_shows_four_items_then_more_and_discount(self):
        """US-11: at most 4 items, "+ N more", and the bulk discount."""
        for wine in self.wines:
            self.add(self.client, wine, 2)
        response = self.client.get(self.url)
        self.assertContains(response, 'class="cart-preview__item"', count=4)
        self.assertContains(response, "+ 2 more")
        self.assertEqual(response.context["totals"].discount, Decimal("12.00"))
        self.assertContains(response, "Discount (8+ bottles)")
        self.assertContains(response, "−€12.00")

    def test_never_shows_another_sessions_cart(self):
        """US-11: each visitor only ever sees their own cart."""
        other = Client()
        self.add(other, self.wines[0], 3)
        response = self.client.get(self.url)
        self.assertContains(response, "Your cart is empty.")
        self.assertNotContains(response, "Preview Wine 0")

    def test_not_cached_and_get_only(self):
        """US-11: the preview isn't cached and only answers GET."""
        response = self.client.get(self.url)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(self.client.post(self.url).status_code, 405)

    def test_nav_has_preview_trigger(self):
        """US-11: the nav cart icon has the preview panel wired up."""
        response = self.client.get(reverse("wine_list"))
        self.assertContains(response, f'data-url="{self.url}"')
        self.assertContains(
            response,
            'id="cartPreviewPanel" role="region" '
            'aria-label="Cart preview" hidden',
        )


class UpdateCartQuantityTests(TestCase):
    """US-11: Update the quantity of a wine on the cart page."""

    def setUp(self):
        self.client = Client()
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Test Red",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.5,
            price="12.50",
            stock=10,
        )
        self.other = Wine.objects.create(
            name="Test White",
            producer="Test Producer",
            region=region,
            wine_type="white",
            abv=12.0,
            price="15.00",
            stock=10,
        )
        self.client.post(
            reverse("cart_add", args=[self.wine.id]), {"quantity": 2}
        )
        self.url = reverse("cart_update", args=[self.wine.id])

    def quantity(self):
        cart = self.client.session["cart"]
        return cart.get(str(self.wine.id), {}).get("quantity", 0)

    def post_json(self, quantity):
        return self.client.post(
            self.url,
            {"quantity": quantity},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

    def test_update_changes_quantity(self):
        """US-11: Update sets the wine to the chosen quantity."""
        response = self.client.post(self.url, {"quantity": 5}, follow=True)
        self.assertRedirects(response, reverse("cart_detail"))
        self.assertEqual(self.quantity(), 5)
        self.assertContains(response, "updated to 5 bottles")
        self.assertContains(response, "€62.50")

    def test_update_can_lower_quantity(self):
        """US-11: the quantity can go down as well as up."""
        self.client.post(self.url, {"quantity": 1})
        self.assertEqual(self.quantity(), 1)

    def test_quantity_above_stock_is_capped_with_message(self):
        """US-11: more than the stock is capped at the stock, with a note."""
        response = self.client.post(self.url, {"quantity": 50}, follow=True)
        self.assertEqual(self.quantity(), 10)
        self.assertContains(
            response, "Only 10 of &quot;Test Red&quot; in stock."
        )
        self.assertContains(response, "message--warning")

    def test_zero_removes_item(self):
        """US-11: setting the quantity to 0 removes the wine."""
        self.client.post(
            reverse("cart_add", args=[self.other.id]), {"quantity": 1}
        )
        response = self.client.post(self.url, {"quantity": 0}, follow=True)
        cart = self.client.session["cart"]
        self.assertNotIn(str(self.wine.id), cart)
        self.assertIn(str(self.other.id), cart)
        self.assertContains(response, "removed from your cart")

    def test_invalid_values_are_rejected(self):
        """US-11: negative, decimal, text or missing values change nothing."""
        for value in ["-1", "2.5", "abc", ""]:
            with self.subTest(value=value):
                response = self.client.post(
                    self.url, {"quantity": value}, follow=True
                )
                self.assertRedirects(response, reverse("cart_detail"))
                self.assertEqual(self.quantity(), 2)
                self.assertContains(response, "message--error")
        self.client.post(self.url)
        self.assertEqual(self.quantity(), 2)

    def test_wine_not_in_cart_is_rejected(self):
        """US-11: a wine that isn't in the cart can't be updated into it."""
        url = reverse("cart_update", args=[self.other.id])
        response = self.client.post(url, {"quantity": 3})
        self.assertRedirects(response, reverse("cart_detail"))
        self.assertNotIn(str(self.other.id), self.client.session["cart"])

    def test_get_not_allowed(self):
        """US-11: update only accepts POST."""
        response = self.client.get(self.url, {"quantity": 5})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.quantity(), 2)

    def test_update_requires_csrf_token(self):
        """US-11: update is protected by CSRF like the other cart forms."""
        client = Client(enforce_csrf_checks=True)
        response = client.post(self.url, {"quantity": 5})
        self.assertEqual(response.status_code, 403)

    def test_discount_recalculates(self):
        """US-11: going from 8 bottles to 7 removes the 8-bottle discount."""
        self.client.post(self.url, {"quantity": 8})
        totals = self.client.get(reverse("cart_detail")).context["totals"]
        self.assertEqual(totals.discount, Decimal("10.00"))
        self.assertEqual(totals.grand_total, Decimal("90.00"))

        self.client.post(self.url, {"quantity": 7})
        response = self.client.get(reverse("cart_detail"))
        totals = response.context["totals"]
        self.assertEqual(totals.discount, Decimal("0.00"))
        self.assertEqual(totals.grand_total, Decimal("87.50"))
        self.assertNotContains(response, "totals__row--discount")

    def test_json_response_for_fetch(self):
        """US-11: fetch requests get JSON with the new line and totals."""
        response = self.post_json(8)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["level"], "success")
        self.assertEqual(data["quantity"], 8)
        self.assertEqual(data["line_total"], "100.00")
        self.assertEqual(data["subtotal"], "100.00")
        self.assertEqual(data["discount"], "10.00")
        self.assertIsNone(data["delivery"])
        self.assertEqual(data["total"], "90.00")
        self.assertEqual(data["bottle_count"], 8)
        self.assertIn("totals__row--discount", data["totals_html"])
        # The message is in the JSON, not left over for the next page
        page = self.client.get(reverse("cart_detail"))
        self.assertNotContains(page, "updated to 8 bottles")

    def test_json_discount_removed_at_seven(self):
        """US-11: the JSON totals drop the discount going from 8 to 7."""
        self.post_json(8)
        data = self.post_json(7).json()
        self.assertEqual(data["discount"], "0.00")
        self.assertEqual(data["total"], "87.50")
        self.assertNotIn("totals__row--discount", data["totals_html"])

    def test_json_capped_and_removed(self):
        """US-11: JSON reports a stock cap and a removal (quantity 0)."""
        data = self.post_json(50).json()
        self.assertEqual(data["level"], "warning")
        self.assertEqual(data["quantity"], 10)
        self.assertEqual(data["max"], 10)

        data = self.post_json(0).json()
        self.assertEqual(data["quantity"], 0)
        self.assertEqual(data["bottle_count"], 0)
        self.assertEqual(data["total"], "0.00")

    def test_json_invalid_value_returns_400_with_cart_unchanged(self):
        """US-11: an invalid value gets a 400 with the current quantity."""
        response = self.post_json("abc")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["level"], "error")
        self.assertEqual(data["quantity"], 2)

    def test_cart_page_has_labelled_steppers_and_status(self):
        """US-11: each row has a labelled stepper, Update and a status area."""
        response = self.client.get(reverse("cart_detail"))
        self.assertContains(
            response, f'action="{self.url}" class="cart__update"'
        )
        self.assertContains(
            response,
            f'<label for="quantity-{self.wine.id}" class="sr-only">'
            "Quantity for Test Red</label>",
        )
        self.assertContains(response, 'min="1" max="10"')
        self.assertContains(response, ">Update</button>")
        self.assertContains(response, 'role="status" aria-live="polite"')
        self.assertContains(response, "js/cart.js")
