import hashlib
import hmac
import json
import time
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from orders.forms import CheckoutForm
from orders.models import Order, OrderItem
from orders.pricing import calculate_totals, normalise_eircode
from orders.views import _send_order_confirmation_email
from products.models import Wine, Region
from reviews.models import Review

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
        session["cart"] = {
            str(self.wine.id): {"quantity": 1, "price": "20.00"}
        }
        session.save()
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/checkout.html")

    def test_logged_in_user_can_checkout(self):
        """US-12: logged-in user can access the checkout form."""
        self.client.login(username="test@example.com", password="testpass123")
        session = self.client.session
        session["cart"] = {
            str(self.wine.id): {"quantity": 1, "price": "20.00"}
        }
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
            "city": "Cork",
            "eircode": "T12 X70A",
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
        """US-12: a guest submitting a valid checkout reaches payment."""
        response = self.submit_checkout(mock_create)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/payment.html")
        order = Order.objects.get(email="jane@example.com")
        self.assertIsNone(order.user)
        self.assertEqual(str(order.subtotal), "39.98")
        self.assertEqual(str(order.grand_total), "49.93")
        self.assertEqual(order.postcode, "T12 X70A")
        self.assertEqual(order.country, "Ireland")
        session = self.client.session
        self.assertEqual(
            session["guest_order_number"], str(order.order_number)
        )
        self.assertEqual(
            session["cart"][str(self.wine.id)],
            {"quantity": 2, "price": "19.99"},
        )

    @patch("orders.views.stripe.PaymentIntent.create")
    def test_logged_in_valid_checkout_shows_payment_page(self, mock_create):
        """US-12: a logged-in user's valid checkout reaches payment."""
        self.client.login(username="test@example.com", password="testpass123")
        data = dict(self.form_data, save_to_profile="on")
        response = self.submit_checkout(mock_create, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/payment.html")
        order = Order.objects.get(email="jane@example.com")
        self.assertEqual(order.user, self.user)
        self.assertEqual(str(order.grand_total), "49.93")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.postcode, "T12 X70A")
        self.assertEqual(self.user.profile.country, "Ireland")
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
        session["cart"] = {
            str(self.wine.id): {"quantity": 1, "price": "15.00"}
        }
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
        session["cart"] = {
            str(self.wine.id): {"quantity": 1, "price": "10.00"}
        }
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
        self.assertContains(
            response, "Save this delivery information to my profile"
        )


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
            grand_total=10.00,
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

    def test_order_detail_heading_levels_in_order(self):
        """US-03: sections are h2 under the h1, wine names h3 (no skips)."""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.get(self.url)
        for title in ["Status", "Order Items", "Delivery Address", "Contact"]:
            self.assertContains(
                response, f'<h2 class="order-card__heading">{title}</h2>'
            )
        self.assertContains(response, "<h3>Test Wine</h3>")
        self.assertNotContains(response, "<h4")

    def test_sequential_id_does_not_work(self):
        """US-03: a sequential order id returns 404; only the number works."""
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
            grand_total=25.00,
            status="paid",
        )
        self.url = reverse("order_success", args=[self.order.order_number])

    def test_guest_can_view_own_order_via_session(self):
        """US-13: a guest sees confirmation if the order is in session."""
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
            grand_total=90.00,
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
        """US-13: the order is found by intent id if metadata is missing."""
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
            "city": "Cork",
            "eircode": "T12 X70A",
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
            grand_total=30.00,
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
            grand_total=30.00,
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
        self.client.login(
            username="admin@example.com", password="adminpass123"
        )
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
            grand_total=30.00,
            status="pending",
        )
        OrderItem.objects.create(
            order=self.order,
            wine=self.wine,
            quantity=1,
            price_at_purchase=30.00,
        )

    def test_webhook_sends_order_confirmation_email_once(self):
        """US-30: one email per call, to the order email, with its number."""
        _send_order_confirmation_email(self.order)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to[0], "customer@example.com")
        self.assertIn(str(self.order.order_number), email.subject)

        mail.outbox.clear()
        _send_order_confirmation_email(self.order)
        self.assertEqual(len(mail.outbox), 1)


class BulkDiscountTests(TestCase):
    """US-12: 10% off the wine subtotal for 8 bottles or more."""

    def test_discount_applies_at_exactly_8_bottles(self):
        """US-12: 8 bottles get 10% off the subtotal."""
        totals = calculate_totals(Decimal("80.00"), 8)
        self.assertEqual(totals.discount, Decimal("8.00"))
        self.assertEqual(totals.discounted_subtotal, Decimal("72.00"))

    def test_no_discount_at_7_bottles(self):
        """US-12: 7 bottles get no discount."""
        totals = calculate_totals(Decimal("70.00"), 7)
        self.assertEqual(totals.discount, Decimal("0.00"))
        self.assertFalse(totals.has_discount)

    def test_discount_is_rounded_to_the_cent(self):
        """US-12: the discount is a Decimal rounded to the cent."""
        totals = calculate_totals(Decimal("99.95"), 8)
        self.assertEqual(totals.discount, Decimal("10.00"))
        self.assertEqual(totals.grand_total, Decimal("89.95"))


class DeliveryCostTests(TestCase):
    """US-12: Delivery cost by Eircode routing key, free from €100."""

    def test_dublin_eircode_costs_595(self):
        """US-12: a Dublin routing key (D01-D24, D6W) costs €5.95."""
        for eircode in ["D02 X285", "D24 A1B2", "D6W 1234"]:
            totals = calculate_totals(Decimal("40.00"), 2, eircode)
            self.assertEqual(totals.delivery_cost, Decimal("5.95"))
            self.assertEqual(totals.grand_total, Decimal("45.95"))

    def test_other_eircode_costs_995(self):
        """US-12: anywhere else in Ireland costs €9.95."""
        totals = calculate_totals(Decimal("40.00"), 2, "T12 X70A")
        self.assertEqual(totals.delivery_cost, Decimal("9.95"))
        self.assertEqual(totals.grand_total, Decimal("49.95"))

    def test_free_delivery_at_100_after_discount(self):
        """US-12: delivery is free when the discounted total is €100+."""
        totals = calculate_totals(Decimal("112.00"), 8, "T12 X70A")
        self.assertEqual(totals.discounted_subtotal, Decimal("100.80"))
        self.assertEqual(totals.delivery_cost, Decimal("0.00"))
        self.assertEqual(totals.grand_total, Decimal("100.80"))

    def test_free_delivery_uses_the_discounted_total(self):
        """US-12: €110 before a 10% discount is €99, so delivery is paid."""
        totals = calculate_totals(Decimal("110.00"), 8, "D02 X285")
        self.assertEqual(totals.discounted_subtotal, Decimal("99.00"))
        self.assertEqual(totals.delivery_cost, Decimal("5.95"))
        self.assertEqual(totals.grand_total, Decimal("104.95"))

    def test_delivery_unknown_without_eircode(self):
        """US-11: without an Eircode, delivery is unknown unless it's free."""
        self.assertIsNone(calculate_totals(Decimal("40.00"), 2).delivery_cost)
        self.assertEqual(
            calculate_totals(Decimal("120.00"), 2).delivery_cost,
            Decimal("0.00"),
        )


class EircodeValidationTests(TestCase):
    """US-12: Eircodes are validated and stored normalised."""

    def test_valid_eircodes_are_normalised(self):
        """US-12: any case, with or without a space, becomes "D02 X285"."""
        cases = {
            "D02 X285": "D02 X285",
            "d02x285": "D02 X285",
            "  a65 f4e2 ": "A65 F4E2",
            "d6w1234": "D6W 1234",
        }
        for raw, expected in cases.items():
            self.assertEqual(normalise_eircode(raw), expected)

    def test_invalid_eircodes_are_rejected(self):
        """US-12: wrong length, letters or format are not valid Eircodes."""
        for raw in [
            "", "12345", "D02 X28", "D02 X2855", "B12 3456", "DO2 X285",
        ]:
            self.assertIsNone(normalise_eircode(raw))

    def test_checkout_form_shows_error_for_invalid_eircode(self):
        """US-12: the checkout form explains an invalid Eircode."""
        form = CheckoutForm(data=dict(CHECKOUT_DATA, eircode="12345"))
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Please enter a valid Eircode", form.errors["eircode"][0]
        )

    def test_checkout_form_normalises_eircode(self):
        """US-12: the checkout form accepts lowercase without a space."""
        form = CheckoutForm(data=dict(CHECKOUT_DATA, eircode="d02x285"))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["eircode"], "D02 X285")


CHECKOUT_DATA = {
    "full_name": "Aoife Byrne",
    "email": "aoife@example.com",
    "address_line1": "1 Grafton Street",
    "address_line2": "",
    "city": "Dublin",
    "eircode": "D02 X285",
}


class CheckoutTotalsTests(TestCase):
    """US-12 / US-13: Checkout stores totals and charges the grand total."""

    def setUp(self):
        self.client = Client()
        region = Region.objects.create(name="Test", country="Ireland")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.5,
            price="12.50",
            stock=20,
        )

    def fill_cart(self, quantity):
        self.client.post(
            reverse("cart_add", args=[self.wine.id]), {"quantity": quantity}
        )

    @patch("orders.views.stripe.PaymentIntent.create")
    def test_payment_intent_amount_equals_grand_total(self, mock_create):
        """US-13: Stripe is charged the server-side grand total in cents."""
        mock_create.return_value = MagicMock(
            id="pi_totals", client_secret="pi_totals_secret"
        )
        self.fill_cart(8)
        # Values posted by the browser for totals are ignored
        data = dict(CHECKOUT_DATA, grand_total="1.00", discount="99")
        response = self.client.post(reverse("checkout"), data)

        order = Order.objects.get(email="aoife@example.com")
        self.assertEqual(order.subtotal, Decimal("100.00"))
        self.assertEqual(order.discount, Decimal("10.00"))
        self.assertEqual(order.delivery_cost, Decimal("5.95"))
        self.assertEqual(order.grand_total, Decimal("95.95"))
        self.assertEqual(mock_create.call_args.kwargs["amount"], 9595)
        self.assertContains(response, "Pay €95.95")

    @patch("orders.views.stripe.PaymentIntent.create")
    def test_invalid_eircode_shows_error_and_creates_no_order(
        self, mock_create
    ):
        """US-12: an invalid Eircode is shown as an error; nothing is paid."""
        self.fill_cart(2)
        response = self.client.post(
            reverse("checkout"), dict(CHECKOUT_DATA, eircode="ABC")
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/checkout.html")
        self.assertContains(response, "Please enter a valid Eircode")
        self.assertFalse(Order.objects.exists())
        mock_create.assert_not_called()

    @patch("orders.views.stripe.PaymentIntent.create")
    def test_lowercase_eircode_is_stored_normalised(self, mock_create):
        """US-12: "t12x70a" is saved as "T12 X70A" with €9.95 delivery."""
        mock_create.return_value = MagicMock(id="pi_x", client_secret="s")
        self.fill_cart(2)
        self.client.post(
            reverse("checkout"), dict(CHECKOUT_DATA, eircode="t12x70a")
        )
        order = Order.objects.get(email="aoife@example.com")
        self.assertEqual(order.postcode, "T12 X70A")
        self.assertEqual(order.delivery_cost, Decimal("9.95"))
        self.assertEqual(order.grand_total, Decimal("34.95"))

    def test_checkout_prefills_eircode_from_profile(self):
        """US-12: a saved Eircode on the profile pre-fills the checkout."""
        user = get_user_model().objects.create_user(
            email="saved@example.com", username="saved", password="x"
        )
        user.profile.postcode = "d02x285"
        user.profile.save()
        self.client.force_login(user)
        self.fill_cart(1)
        response = self.client.get(reverse("checkout"))
        initial = response.context["form"].initial
        self.assertEqual(initial["eircode"], "D02 X285")

    def test_checkout_summary_shows_discount_at_8_bottles(self):
        """US-12: the checkout summary shows the bulk discount."""
        self.fill_cart(8)
        response = self.client.get(reverse("checkout"))
        self.assertContains(response, "Discount")
        self.assertContains(response, "−€10.00")
        self.assertContains(response, "Calculated from your Eircode")


class OrderBreakdownDisplayTests(TestCase):
    """US-13 / US-30: The full breakdown on success, detail and email."""

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            email="buyer@example.com", username="buyer", password="x"
        )
        region = Region.objects.create(name="Test", country="Ireland")
        wine = Wine.objects.create(
            name="Test Wine", producer="Test", region=region,
            wine_type="red", abv=13.5, price="12.50", stock=20,
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name="Buyer",
            email="buyer@example.com",
            address_line1="1 Grafton Street",
            city="Dublin",
            postcode="D02 X285",
            country="Ireland",
            subtotal=Decimal("100.00"),
            discount=Decimal("10.00"),
            delivery_cost=Decimal("5.95"),
            grand_total=Decimal("95.95"),
            status="paid",
        )
        OrderItem.objects.create(
            order=self.order, wine=wine, quantity=8,
            price_at_purchase=Decimal("12.50"),
        )

    def assert_breakdown(self, content):
        for text in ["€100.00", "10.00", "€5.95", "€95.95"]:
            self.assertIn(text, content)

    def test_success_page_shows_breakdown(self):
        """US-13: the order success page shows the full breakdown."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("order_success", args=[self.order.order_number])
        )
        self.assert_breakdown(response.content.decode())

    def test_order_detail_shows_breakdown(self):
        """US-03: the order detail page shows the full breakdown."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("order_detail", args=[self.order.order_number])
        )
        self.assert_breakdown(response.content.decode())
        self.assertContains(response, "D02 X285")

    def test_confirmation_email_shows_breakdown(self):
        """US-30: the confirmation email shows the full breakdown."""
        _send_order_confirmation_email(self.order)
        email = mail.outbox[0]
        self.assert_breakdown(email.body)
        self.assert_breakdown(email.alternatives[0][0])


class OrderReviewButtonTests(TestCase):
    """US-03 / US-18: Review buttons on the customer's order page."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="reviewer@example.com", username="reviewer", password="x"
        )
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Button Red", producer="Test", region=region,
            wine_type="red", abv=13.5, price="20.00", stock=10,
        )
        self.client.force_login(self.user)

    def order_with_wine(self, status):
        order = Order.objects.create(
            user=self.user, full_name="R", email="reviewer@example.com",
            address_line1="1 Main St", city="Dublin", postcode="D02 X285",
            country="Ireland", grand_total="20.00", status=status,
        )
        OrderItem.objects.create(
            order=order, wine=self.wine, quantity=1,
            price_at_purchase="20.00",
        )
        return order

    def detail(self, order):
        return self.client.get(
            reverse("order_detail", args=[order.order_number])
        )

    def test_button_for_paid_shipped_and_delivered_orders(self):
        """US-18: paid, shipped and delivered orders offer a review."""
        for status in ["paid", "shipped", "delivered"]:
            with self.subTest(status=status):
                order = self.order_with_wine(status)
                response = self.detail(order)
                self.assertContains(response, "Write a review")
                self.assertContains(
                    response,
                    'data-url="' + reverse(
                        "order_review",
                        args=[order.order_number, self.wine.id],
                    ) + '"',
                )
                self.assertContains(response, 'id="reviewModal"')

    def test_no_button_for_pending_or_cancelled_orders(self):
        """US-18: unpaid orders show no review button or modal."""
        for status in ["pending", "cancelled"]:
            with self.subTest(status=status):
                response = self.detail(self.order_with_wine(status))
                self.assertNotContains(response, "Write a review")
                self.assertNotContains(response, 'id="reviewModal"')

    def test_edit_label_when_already_reviewed_in_every_order(self):
        """US-18: an existing review shows "Edit your review" everywhere."""
        first = self.order_with_wine("paid")
        second = self.order_with_wine("delivered")
        review = Review.objects.create(
            wine=self.wine, user=self.user, rating=4, title="Nice",
            body="From the wine page.",
        )
        edit_url = reverse("edit_review", args=[review.id])
        for order in [first, second]:
            with self.subTest(order=order.pk):
                response = self.detail(order)
                self.assertContains(response, "Edit your review")
                self.assertNotContains(response, "Write a review")
                self.assertContains(response, f'data-url="{edit_url}"')
                self.assertContains(response, 'data-rating="4"')

    def test_buttons_link_to_review_pages_without_javascript(self):
        """US-18: without JavaScript the button opens the review page."""
        order = self.order_with_wine("paid")
        order_path = reverse("order_detail", args=[order.order_number])
        response = self.detail(order)
        fallback = reverse("add_review", args=[self.wine.id])
        self.assertContains(
            response, f'href="{fallback}?next={order_path}"'
        )
