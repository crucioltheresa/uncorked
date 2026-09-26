from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from orders.models import Order, OrderItem
from orders.views import _send_order_confirmation_email
from products.models import Wine, Region

User = get_user_model()


class CheckoutTests(TestCase):
    """US-12: Guest and logged-in checkout."""

    def setUp(self):
        self.client = Client()
        self.region = Region.objects.create(name="Test", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test Producer",
            region=self.region,
            wine_type="red",
            abv=13.50,
            price=20.00,
            stock=100,
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )

    def test_empty_cart_redirects_from_checkout(self):
        """US-12: empty cart redirects to the wine list."""
        response = self.client.get(reverse("checkout"))
        self.assertRedirects(response, reverse("wine_list"))

    def test_guest_can_checkout(self):
        """US-12: guest can access the checkout form."""
        session = self.client.session
        session["cart"] = {str(self.wine.id): {"quantity": 1, "price": "20.00"}}
        session.save()
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/checkout.html")

    def test_logged_in_user_can_checkout(self):
        """US-12: logged-in user can access the checkout form."""
        self.client.login(username="test@example.com", password="testpass123")
        session = self.client.session
        session["cart"] = {str(self.wine.id): {"quantity": 1, "price": "20.00"}}
        session.save()
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 200)


class GuestCheckoutTests(TestCase):
    """US-12: Guest checkout form."""

    def setUp(self):
        self.client = Client()
        self.region = Region.objects.create(name="Test Region", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test Producer",
            region=self.region,
            wine_type="red",
            abv=13.50,
            price=15.00,
            stock=100,
            is_available=True,
        )

    def test_guest_checkout_form_no_save_checkbox(self):
        """US-12: guest checkout form hides the save-to-profile checkbox."""
        session = self.client.session
        session["cart"] = {str(self.wine.id): {"quantity": 1, "price": "15.00"}}
        session.save()

        response = self.client.get(reverse("checkout"))
        self.assertNotContains(response, "save_to_profile")


class CheckoutPrefilledTests(TestCase):
    """US-12: Checkout pre-filled from the user's profile."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.profile = self.user.profile
        self.profile.full_name = "John Doe"
        self.profile.address_line1 = "123 Main St"
        self.profile.city = "New York"
        self.profile.postcode = "10001"
        self.profile.country = "USA"
        self.profile.save()
        self.region = Region.objects.create(name="Test Region", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test Producer",
            region=self.region,
            wine_type="red",
            abv=13.50,
            price=10.00,
            stock=100,
            is_available=True,
        )
        self.client.login(email="test@example.com", password="testpass123")
        session = self.client.session
        session["cart"] = {str(self.wine.id): {"quantity": 1, "price": "10.00"}}
        session.save()

    def test_checkout_prefilled_with_saved_details(self):
        """US-12: checkout form is pre-filled with saved profile details."""
        response = self.client.get(reverse("checkout"))
        form = response.context["form"]
        self.assertEqual(form.initial["full_name"], "John Doe")
        self.assertEqual(form.initial["city"], "New York")

    def test_save_to_profile_checkbox_shown_when_logged_in(self):
        """US-12: save-to-profile checkbox appears for logged-in users."""
        response = self.client.get(reverse("checkout"))
        self.assertContains(response, "save_to_profile")
        self.assertContains(response, "Save this delivery information to my profile")


class OrderDetailViewTests(TestCase):
    """US-03: Order detail page, private to the order owner."""

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
        self.region = Region.objects.create(name="Test Region", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test Producer",
            region=self.region,
            wine_type="red",
            abv=13.50,
            price=10.00,
            stock=100,
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name="John Doe",
            email="john@example.com",
            address_line1="123 Main St",
            city="New York",
            postcode="10001",
            country="USA",
            total_price=10.00,
            status="paid",
        )
        OrderItem.objects.create(
            order=self.order,
            wine=self.wine,
            quantity=1,
            price_at_purchase=10.00,
        )
        self.url = reverse("order_detail", args=[self.order.order_number])

    def test_order_detail_requires_login(self):
        """US-03: order detail redirects anonymous users to login."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_user_can_see_own_order(self):
        """US-03: user can see their own order by order number."""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Order #{self.order.order_number}")

    def test_user_cannot_see_other_user_order(self):
        """US-03: user cannot see another user's order."""
        self.client.login(username="other@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_order_detail_shows_items(self):
        """US-03: order detail lists the wines in the order."""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertContains(response, "Test Wine")

    def test_sequential_id_does_not_work(self):
        """US-03: sequential order id returns 404, only the order number works."""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.get(f"/order/{self.order.id}/")
        self.assertEqual(response.status_code, 404)


class GuestOrderAccessTests(TestCase):
    """US-13: Guest sees the order confirmation page via session."""

    def setUp(self):
        self.client = Client()
        self.order = Order.objects.create(
            full_name="Guest",
            email="guest@example.com",
            address_line1="456 Oak",
            city="Boston",
            postcode="02101",
            country="USA",
            total_price=25.00,
            status="paid",
        )
        self.url = reverse("order_success", args=[self.order.order_number])

    def test_guest_can_view_own_order_via_session(self):
        """US-13: guest sees the confirmation page if the order is in session."""
        session = self.client.session
        session["guest_order_number"] = str(self.order.order_number)
        session.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_guest_cannot_view_order_not_in_session(self):
        """US-13: guest cannot see an order that is not in their session."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class PaymentProcessingTests(TestCase):
    """US-13: Order status and stock after payment."""

    def setUp(self):
        self.region = Region.objects.create(name="Test", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test",
            region=self.region,
            wine_type="red",
            abv=13.5,
            price=30.00,
            stock=100,
        )

    def test_order_status_can_be_marked_paid(self):
        """US-13: order status can transition to paid."""
        order = Order.objects.create(
            full_name="Customer",
            email="customer@example.com",
            address_line1="123 Main",
            city="City",
            postcode="12345",
            country="USA",
            total_price=30.00,
            status="pending",
        )
        order.status = "paid"
        order.save()
        order.refresh_from_db()
        self.assertEqual(order.status, "paid")

    def test_stock_can_be_reduced_after_payment(self):
        """US-13: stock is reduced when an order is paid."""
        wine = self.wine
        wine.stock = 10
        wine.save()

        OrderItem.objects.create(
            order=Order.objects.create(
                full_name="Customer",
                email="customer@example.com",
                address_line1="123 Main",
                city="City",
                postcode="12345",
                country="USA",
                total_price=30.00,
                status="paid",
            ),
            wine=wine,
            quantity=3,
            price_at_purchase=30.00,
        )

        wine.stock -= 3
        wine.save()
        wine.refresh_from_db()
        self.assertEqual(wine.stock, 7)


class OrderConfirmationEmailTests(TestCase):
    """US-30: Order confirmation email."""

    def setUp(self):
        self.region = Region.objects.create(name="Test Region", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test Producer",
            region=self.region,
            wine_type="red",
            abv=13.50,
            price=20.00,
            stock=100,
            is_available=True,
        )
        self.order = Order.objects.create(
            full_name="Customer Name",
            email="customer@example.com",
            address_line1="123 Main St",
            city="New York",
            postcode="10001",
            country="USA",
            total_price=30.00,
            status="pending",
        )
        OrderItem.objects.create(
            order=self.order,
            wine=self.wine,
            quantity=1,
            price_at_purchase=30.00,
        )

    def test_webhook_sends_order_confirmation_email_once(self):
        """US-30: one email per call, sent to the order email with its number."""
        _send_order_confirmation_email(self.order)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to[0], "customer@example.com")
        self.assertIn(str(self.order.order_number), email.subject)

        mail.outbox.clear()
        _send_order_confirmation_email(self.order)
        self.assertEqual(len(mail.outbox), 1)
