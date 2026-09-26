from unittest.mock import patch

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


class StripeWebhookTests(TestCase):
    """US-13: Payment confirmation via the Stripe webhook."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("stripe_webhook")
        region = Region.objects.create(name="Test", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test",
            region=region,
            wine_type="red",
            abv=13.5,
            price=30.00,
            stock=10,
        )
        self.order = Order.objects.create(
            full_name="Customer",
            email="customer@example.com",
            address_line1="123 Main",
            city="City",
            postcode="12345",
            country="USA",
            total_price=90.00,
            status="pending",
        )
        OrderItem.objects.create(
            order=self.order,
            wine=self.wine,
            quantity=3,
            price_at_purchase=30.00,
        )
        self.event = {
            "type": "payment_intent.succeeded",
            "data": {"object": {
                "metadata": {"order_number": str(self.order.order_number)},
            }},
        }

    def post_webhook(self):
        return self.client.post(
            self.url, data="{}", content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test-signature",
        )

    @patch("orders.views.stripe.Webhook.construct_event")
    def test_webhook_marks_order_paid(self, mock_construct):
        """US-13: successful payment webhook marks the order as paid."""
        mock_construct.return_value = self.event
        response = self.post_webhook()
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    @patch("orders.views.stripe.Webhook.construct_event")
    def test_webhook_reduces_stock(self, mock_construct):
        """US-13: successful payment webhook reduces wine stock."""
        mock_construct.return_value = self.event
        self.post_webhook()
        self.wine.refresh_from_db()
        self.assertEqual(self.wine.stock, 7)

    @patch("orders.views.stripe.Webhook.construct_event")
    def test_webhook_sends_confirmation_email(self, mock_construct):
        """US-30: successful payment webhook emails the customer."""
        mock_construct.return_value = self.event
        self.post_webhook()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["customer@example.com"])

    @patch("orders.views.stripe.Webhook.construct_event")
    def test_invalid_signature_returns_400(self, mock_construct):
        """US-13: webhook with an invalid payload returns 400."""
        mock_construct.side_effect = ValueError("bad payload")
        response = self.post_webhook()
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")


class PaymentFailureTests(TestCase):
    """US-14: Payment failure."""

    def setUp(self):
        self.client = Client()
        region = Region.objects.create(name="Test", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test",
            region=region,
            wine_type="red",
            abv=13.5,
            price=30.00,
            stock=10,
        )
        self.order = Order.objects.create(
            full_name="Customer",
            email="customer@example.com",
            address_line1="123 Main",
            city="City",
            postcode="12345",
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
        self.event = {
            "type": "payment_intent.payment_failed",
            "data": {"object": {
                "metadata": {"order_number": str(self.order.order_number)},
            }},
        }

    @patch("orders.views.stripe.Webhook.construct_event")
    def test_failed_payment_keeps_order_pending(self, mock_construct):
        """US-14: failed payment leaves the order pending."""
        mock_construct.return_value = self.event
        self.client.post(
            reverse("stripe_webhook"), data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test-signature",
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    @patch("orders.views.stripe.Webhook.construct_event")
    def test_failed_payment_keeps_stock(self, mock_construct):
        """US-14: failed payment does not reduce stock or send an email."""
        mock_construct.return_value = self.event
        self.client.post(
            reverse("stripe_webhook"), data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test-signature",
        )
        self.wine.refresh_from_db()
        self.assertEqual(self.wine.stock, 10)
        self.assertEqual(len(mail.outbox), 0)


class AdminOrdersTests(TestCase):
    """US-15: Admin order management is staff-only."""

    def setUp(self):
        self.client = Client()
        self.customer = User.objects.create_user(
            email="customer@example.com",
            username="customer",
            password="testpass123",
        )
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass123",
        )
        Order.objects.create(
            full_name="Customer Name",
            email="customer@example.com",
            address_line1="123 Main",
            city="City",
            postcode="12345",
            country="USA",
            total_price=30.00,
            status="paid",
        )
        self.orders_url = reverse("admin:orders_order_changelist")

    def test_non_staff_cannot_access_admin(self):
        """US-15: non-staff users are sent to the admin login page."""
        self.client.login(
            username="customer@example.com", password="testpass123"
        )
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/admin/login/"))

    def test_non_staff_cannot_access_order_admin(self):
        """US-15: non-staff users cannot open the admin order list."""
        self.client.login(
            username="customer@example.com", password="testpass123"
        )
        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, 302)

    def test_staff_can_see_orders_in_admin(self):
        """US-15: staff can see orders in the admin order list."""
        self.client.login(username="admin@example.com", password="adminpass123")
        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customer Name")


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
