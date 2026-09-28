import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock, patch

from django.test import TestCase, Client, override_settings
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


class CheckoutSubmitTests(TestCase):
    """US-12: Submitting the checkout form."""

    def setUp(self):
        self.client = Client()
        region = Region.objects.create(name="Test", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.50,
            price="19.99",
            stock=100,
        )
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.form_data = {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "address_line1": "1 Vine Street",
            "address_line2": "",
            "city": "Lisbon",
            "postcode": "1000-001",
            "country": "Portugal",
        }

    def submit_checkout(self, mock_create, data=None):
        mock_create.return_value = MagicMock(
            id="pi_test", client_secret="pi_test_secret"
        )
        self.client.post(
            reverse("cart_add", args=[self.wine.id]), {"quantity": 2}
        )
        return self.client.post(reverse("checkout"), data or self.form_data)

    @patch("orders.views.stripe.PaymentIntent.create")
    def test_guest_valid_checkout_shows_payment_page(self, mock_create):
        """US-12: guest submitting a valid checkout reaches the payment page."""
        response = self.submit_checkout(mock_create)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/payment.html")
        order = Order.objects.get(email="jane@example.com")
        self.assertIsNone(order.user)
        self.assertEqual(str(order.total_price), "39.98")
        session = self.client.session
        self.assertEqual(session["guest_order_number"], str(order.order_number))
        self.assertEqual(
            session["cart"][str(self.wine.id)],
            {"quantity": 2, "price": "19.99"},
        )

    @patch("orders.views.stripe.PaymentIntent.create")
    def test_logged_in_valid_checkout_shows_payment_page(self, mock_create):
        """US-12: logged-in user submitting a valid checkout reaches payment."""
        self.client.login(username="test@example.com", password="testpass123")
        data = dict(self.form_data, save_to_profile="on")
        response = self.submit_checkout(mock_create, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/payment.html")
        order = Order.objects.get(email="jane@example.com")
        self.assertEqual(order.user, self.user)
        self.assertEqual(str(order.total_price), "39.98")
        self.assertEqual(
            self.client.session["cart"][str(self.wine.id)],
            {"quantity": 2, "price": "19.99"},
        )


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


WEBHOOK_SECRET = "whsec_test_secret"


def signed_webhook_post(client, event_type, intent, secret=WEBHOOK_SECRET):
    """POST a Stripe event signed the same way Stripe signs real ones."""
    payload = json.dumps({
        "id": "evt_test",
        "object": "event",
        "type": event_type,
        "data": {"object": intent},
    })
    timestamp = int(time.time())
    signature = hmac.new(
        secret.encode(), f"{timestamp}.{payload}".encode(), hashlib.sha256
    ).hexdigest()
    return client.post(
        reverse("stripe_webhook"),
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={signature}",
    )


def payment_intent(order_number, intent_id="pi_test_123"):
    """A PaymentIntent with the metadata the checkout sends."""
    return {
        "id": intent_id,
        "object": "payment_intent",
        "amount": 9000,
        "currency": "eur",
        "status": "succeeded",
        "metadata": {"order_number": order_number},
    }


@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
class StripeWebhookTests(TestCase):
    """US-13: Payment confirmation via the Stripe webhook."""

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
            total_price=90.00,
            status="pending",
            stripe_payment_intent="pi_test_123",
        )
        OrderItem.objects.create(
            order=self.order,
            wine=self.wine,
            quantity=3,
            price_at_purchase=30.00,
        )
        self.intent = payment_intent(str(self.order.order_number))

    def test_webhook_marks_order_paid(self):
        """US-13: successful payment webhook marks the order as paid."""
        response = signed_webhook_post(
            self.client, "payment_intent.succeeded", self.intent
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    def test_webhook_reduces_stock(self):
        """US-13: successful payment webhook reduces wine stock."""
        signed_webhook_post(
            self.client, "payment_intent.succeeded", self.intent
        )
        self.wine.refresh_from_db()
        self.assertEqual(self.wine.stock, 7)

    def test_webhook_sends_confirmation_email(self):
        """US-30: successful payment webhook emails the customer."""
        signed_webhook_post(
            self.client, "payment_intent.succeeded", self.intent
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["customer@example.com"])

    def test_repeated_event_is_processed_once(self):
        """US-13: a retried event does not reduce stock or email twice."""
        for _ in range(2):
            response = signed_webhook_post(
                self.client, "payment_intent.succeeded", self.intent
            )
            self.assertEqual(response.status_code, 200)
        self.wine.refresh_from_db()
        self.assertEqual(self.wine.stock, 7)
        self.assertEqual(len(mail.outbox), 1)

    def test_order_found_by_intent_id_without_metadata(self):
        """US-13: order is found by payment intent id if metadata is missing."""
        intent = dict(self.intent, metadata={})
        signed_webhook_post(self.client, "payment_intent.succeeded", intent)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    def test_unknown_order_returns_200_and_logs_warning(self):
        """US-13: an unknown order number is logged and nothing changes."""
        intent = payment_intent("not-a-uuid", intent_id="pi_unknown")
        with self.assertLogs("orders.views", level="WARNING") as logs:
            response = signed_webhook_post(
                self.client, "payment_intent.succeeded", intent
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn("no order for payment intent pi_unknown", logs.output[0])
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_webhook_logs_each_step(self):
        """US-13: event, paid order and sent email are logged."""
        with self.assertLogs("orders.views", level="INFO") as logs:
            signed_webhook_post(
                self.client, "payment_intent.succeeded", self.intent
            )
        output = "\n".join(logs.output)
        self.assertIn("webhook received: payment_intent.succeeded", output)
        self.assertIn("marked paid", output)
        self.assertIn("confirmation email sent", output)

    def test_invalid_signature_returns_400(self):
        """US-13: webhook with an invalid signature returns 400."""
        response = signed_webhook_post(
            self.client,
            "payment_intent.succeeded",
            self.intent,
            secret="whsec_wrong",
        )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")


@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
class CheckoutToWebhookTests(TestCase):
    """US-13: The webhook reads exactly what the checkout sends to Stripe."""

    def setUp(self):
        self.client = Client()
        region = Region.objects.create(name="Test", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.50,
            price="20.00",
            stock=10,
        )

    @patch("orders.views.stripe.PaymentIntent.create")
    def test_checkout_metadata_marks_order_paid(self, mock_create):
        """US-13: the checkout's own PaymentIntent metadata marks it paid."""
        mock_create.return_value = MagicMock(
            id="pi_from_checkout", client_secret="pi_from_checkout_secret"
        )
        self.client.post(
            reverse("cart_add", args=[self.wine.id]), {"quantity": 2}
        )
        self.client.post(reverse("checkout"), {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "address_line1": "1 Vine Street",
            "city": "Lisbon",
            "postcode": "1000-001",
            "country": "Portugal",
        })
        sent = mock_create.call_args.kwargs
        intent = {
            "id": "pi_from_checkout",
            "object": "payment_intent",
            "amount": sent["amount"],
            "currency": sent["currency"],
            "status": "succeeded",
            "metadata": sent["metadata"],
        }

        response = signed_webhook_post(
            self.client, "payment_intent.succeeded", intent
        )

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(email="jane@example.com")
        self.assertEqual(order.stripe_payment_intent, "pi_from_checkout")
        self.assertEqual(order.status, "paid")
        self.wine.refresh_from_db()
        self.assertEqual(self.wine.stock, 8)
        self.assertEqual(len(mail.outbox), 1)


@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
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
        self.intent = payment_intent(str(self.order.order_number))

    def test_failed_payment_keeps_order_pending(self):
        """US-14: failed payment leaves the order pending."""
        signed_webhook_post(
            self.client, "payment_intent.payment_failed", self.intent
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_failed_payment_keeps_stock(self):
        """US-14: failed payment does not reduce stock or send an email."""
        signed_webhook_post(
            self.client, "payment_intent.payment_failed", self.intent
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
