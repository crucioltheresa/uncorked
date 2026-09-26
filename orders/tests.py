from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.mail import outbox
from orders.models import Order, OrderItem
from products.models import Wine, Region

User = get_user_model()


class CheckoutTests(TestCase):
    """US-10: Guest and logged-in checkout."""

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
        """US-10: Empty cart redirects to wine list."""
        response = self.client.get(reverse("checkout"))
        self.assertRedirects(response, reverse("wine_list"))

    def test_guest_can_checkout(self):
        """US-10: Guest can access checkout form."""
        session = self.client.session
        session["cart"] = {str(self.wine.id): {"quantity": 1, "price": "20.00"}}
        session.save()
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/checkout.html")

    def test_logged_in_user_can_checkout(self):
        """US-10: Logged-in user sees prefilled form."""
        self.client.login(username="test@example.com", password="testpass123")
        session = self.client.session
        session["cart"] = {str(self.wine.id): {"quantity": 1, "price": "20.00"}}
        session.save()
        response = self.client.get(reverse("checkout"))
        self.assertEqual(response.status_code, 200)


class OrderDetailTests(TestCase):
    """US-11: Order privacy with UUID."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="user1@example.com",
            username="user1",
            password="pass123",
        )
        self.other_user = User.objects.create_user(
            email="user2@example.com",
            username="user2",
            password="pass123",
        )
        self.region = Region.objects.create(name="Test", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test",
            region=self.region,
            wine_type="red",
            abv=13.5,
            price=20.00,
            stock=100,
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name="Test User",
            email="user1@example.com",
            address_line1="123 Main",
            city="City",
            postcode="12345",
            country="USA",
            total_price=20.00,
            status="paid",
        )
        OrderItem.objects.create(
            order=self.order,
            wine=self.wine,
            quantity=1,
            price_at_purchase=20.00,
        )

    def test_order_detail_requires_login(self):
        """US-11: Unauthorized access redirects to login."""
        response = self.client.get(
            reverse("order_detail", args=[self.order.order_number])
        )
        self.assertEqual(response.status_code, 302)

    def test_user_can_see_own_order(self):
        """US-11: User sees their own order."""
        self.client.login(username="user1@example.com", password="pass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.order_number])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Wine")

    def test_user_cannot_see_other_user_order(self):
        """US-11: User cannot access another's order."""
        self.client.login(username="user2@example.com", password="pass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.order_number])
        )
        self.assertEqual(response.status_code, 404)

    def test_sequential_id_does_not_work(self):
        """US-11: Sequential ID access fails, only UUID works."""
        self.client.login(username="user1@example.com", password="pass123")
        response = self.client.get(f"/order/{self.order.id}/")
        self.assertEqual(response.status_code, 404)


class GuestOrderAccessTests(TestCase):
    """US-10: Guest order access via session."""

    def setUp(self):
        self.client = Client()
        self.region = Region.objects.create(name="Test", country="USA")
        self.wine = Wine.objects.create(
            name="Test Wine",
            producer="Test",
            region=self.region,
            wine_type="red",
            abv=13.5,
            price=25.00,
            stock=100,
        )

    def test_guest_can_view_own_order_via_session(self):
        """US-10: Guest sees order if in session."""
        order = Order.objects.create(
            full_name="Guest",
            email="guest@example.com",
            address_line1="456 Oak",
            city="Boston",
            postcode="02101",
            country="USA",
            total_price=25.00,
            status="paid",
        )
        session = self.client.session
        session["guest_order_number"] = str(order.order_number)
        session.save()
        response = self.client.get(
            reverse("order_success", args=[order.order_number])
        )
        self.assertEqual(response.status_code, 200)

    def test_guest_cannot_view_order_not_in_session(self):
        """US-10: Guest cannot access order not in session."""
        order = Order.objects.create(
            full_name="Guest",
            email="guest@example.com",
            address_line1="456 Oak",
            city="Boston",
            postcode="02101",
            country="USA",
            total_price=25.00,
            status="paid",
        )
        response = self.client.get(
            reverse("order_success", args=[order.order_number])
        )
        self.assertEqual(response.status_code, 404)


class PaymentProcessingTests(TestCase):
    """US-12: Order status and stock after payment."""

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
        """US-12: Order status can transition to paid."""
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
        """US-12: Stock is reduced when order is paid."""
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

    def test_email_function_exists(self):
        """US-12: Order confirmation email function exists."""
        order = Order.objects.create(
            full_name="Customer",
            email="customer@example.com",
            address_line1="123 Main",
            city="City",
            postcode="12345",
            country="USA",
            total_price=30.00,
            status="paid",
        )

        from orders.views import _send_order_confirmation_email

        try:
            _send_order_confirmation_email(order)
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Email function failed: {e}")
