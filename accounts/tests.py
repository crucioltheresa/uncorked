from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import UserProfile
from orders.models import Order, OrderItem
from products.models import Wine, Region

User = get_user_model()


class UserProfileModelTests(TestCase):
    """Tests for UserProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )

    def test_profile_auto_created_on_user_creation(self):
        """Profile is auto-created when user is created."""
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.email, self.user.email)

    def test_profile_one_to_one_relationship(self):
        """Each user has exactly one profile."""
        self.assertEqual(self.user.profile.user, self.user)

    def test_profile_str(self):
        """Profile string representation."""
        self.assertEqual(str(self.user.profile), f"Profile for {self.user.email}")


class ProfileViewTests(TestCase):
    """Tests for profile view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.profile_url = reverse("profile")

    def test_profile_requires_login(self):
        """Profile page requires login."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertTrue(response.url.startswith("/accounts/login"))

    def test_profile_accessible_when_logged_in(self):
        """Profile page is accessible when logged in."""
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")

    def test_profile_contains_form(self):
        """Profile page contains delivery details form."""
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.get(self.profile_url)
        self.assertIn("form", response.context)

    def test_profile_update_delivery_details(self):
        """User can update delivery details."""
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.post(
            self.profile_url,
            {
                "full_name": "John Doe",
                "email": "john@example.com",
                "address_line1": "123 Main St",
                "address_line2": "",
                "city": "New York",
                "postcode": "10001",
                "country": "USA",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.full_name, "John Doe")
        self.assertEqual(self.user.profile.city, "New York")

    def test_profile_shows_order_history(self):
        """Profile page shows user's orders."""
        region = Region.objects.create(name="Test Region", country="USA")
        wine = Wine.objects.create(
            name="Test Wine",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.50,
            price=10.00,
            stock=100,
        )
        order = Order.objects.create(
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
            order=order,
            wine=wine,
            quantity=1,
            price_at_purchase=10.00,
        )
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.get(self.profile_url)
        self.assertContains(response, f"Order #{order.id}")
        self.assertContains(response, "€10.00")


class OrderDetailViewTests(TestCase):
    """Tests for order detail view."""

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

    def test_order_detail_requires_login(self):
        """Order detail requires login."""
        url = reverse("order_detail", args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_user_can_see_own_order(self):
        """User can see their own order."""
        self.client.login(email="test@example.com", password="testpass123")
        url = reverse("order_detail", args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Order #{self.order.id}")

    def test_user_cannot_see_other_user_order(self):
        """User cannot see other user's order."""
        self.client.login(email="other@example.com", password="testpass123")
        url = reverse("order_detail", args=[self.order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_order_detail_shows_items(self):
        """Order detail shows order items."""
        self.client.login(email="test@example.com", password="testpass123")
        url = reverse("order_detail", args=[self.order.id])
        response = self.client.get(url)
        self.assertContains(response, "Test Wine")


class CheckoutPrefilledTests(TestCase):
    """Tests for checkout pre-fill from profile."""

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

    def test_checkout_prefilled_with_saved_details(self):
        """Checkout form is pre-filled with saved profile details."""
        self.client.login(email="test@example.com", password="testpass123")
        # Add wine to cart via session
        session = self.client.session
        session["cart"] = {str(self.wine.id): {"quantity": 1, "price": "10.00"}}
        session.save()
        response = self.client.get(reverse("checkout"))
        # Form should have initial data
        form = response.context["form"]
        self.assertEqual(form.initial["full_name"], "John Doe")
        self.assertEqual(form.initial["city"], "New York")

    def test_save_to_profile_checkbox_shown_when_logged_in(self):
        """Save to profile checkbox appears in checkout for logged-in users."""
        self.client.login(email="test@example.com", password="testpass123")
        # Add wine to cart via session
        session = self.client.session
        session["cart"] = {str(self.wine.id): {"quantity": 1, "price": "10.00"}}
        session.save()
        response = self.client.get(reverse("checkout"))
        self.assertContains(response, "save_to_profile")
        self.assertContains(response, "Save this delivery information to my profile")
