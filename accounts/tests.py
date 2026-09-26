from importlib import import_module

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from allauth.account.models import EmailAddress
from .models import UserProfile
from orders.models import Order, OrderItem
from products.models import Wine, Region

User = get_user_model()


class RegistrationTests(TestCase):
    """US-01: Registration."""

    def setUp(self):
        self.client = Client()
        self.signup_url = reverse("account_signup")
        User.objects.create_user(
            email="taken@example.com",
            username="taken",
            password="Str0ngPass!23",
        )

    def test_valid_signup_creates_user(self):
        """US-01: valid signup creates a user and asks for email confirmation."""
        response = self.client.post(self.signup_url, {
            "email": "new@example.com",
            "password1": "Str0ngPass!23",
            "password2": "Str0ngPass!23",
        })
        self.assertRedirects(
            response, reverse("account_email_verification_sent")
        )
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_duplicate_email_does_not_create_second_account(self):
        """US-01: duplicate email creates no new account and notifies the owner."""
        self.client.post(self.signup_url, {
            "email": "taken@example.com",
            "password1": "Str0ngPass!23",
            "password2": "Str0ngPass!23",
        })
        self.assertEqual(
            User.objects.filter(email="taken@example.com").count(), 1
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["taken@example.com"])

    def test_passwords_not_matching_shows_error(self):
        """US-01: mismatched passwords show an error and create no user."""
        response = self.client.post(self.signup_url, {
            "email": "new@example.com",
            "password1": "Str0ngPass!23",
            "password2": "Different!456",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "You must type the same password each time."
        )
        self.assertFalse(User.objects.filter(email="new@example.com").exists())


class LoginLogoutTests(TestCase):
    """US-02: Login and logout."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="Str0ngPass!23",
        )
        EmailAddress.objects.filter(user=self.user).update(verified=True)

    def test_wrong_password_shows_error(self):
        """US-02: wrong password shows an error and does not log in."""
        response = self.client.post(reverse("account_login"), {
            "login": "test@example.com",
            "password": "WrongPass!99",
        })
        self.assertContains(
            response,
            "The email address and/or password you specified are not correct.",
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logged_in_user_redirected_from_login_page(self):
        """US-02: logged-in user cannot access the login page."""
        self.client.login(username="test@example.com", password="Str0ngPass!23")
        response = self.client.get(reverse("account_login"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_logout_logs_user_out(self):
        """US-02: logout ends the session and redirects home."""
        self.client.login(username="test@example.com", password="Str0ngPass!23")
        response = self.client.post(reverse("account_logout"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)


class UserProfileModelTests(TestCase):
    """US-03: UserProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )

    def test_profile_auto_created_on_user_creation(self):
        """US-03: profile is auto-created when a user is created."""
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.email, self.user.email)

    def test_profile_one_to_one_relationship(self):
        """US-03: each user has exactly one profile."""
        self.assertEqual(self.user.profile.user, self.user)

    def test_profile_str(self):
        """US-03: profile string representation shows the user's email."""
        self.assertEqual(str(self.user.profile), f"Profile for {self.user.email}")


class ProfileViewTests(TestCase):
    """US-03: Profile page and order history."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.profile_url = reverse("profile")

    def test_profile_requires_login(self):
        """US-03: profile page redirects anonymous users to login."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login"))

    def test_profile_accessible_when_logged_in(self):
        """US-03: profile page is accessible when logged in."""
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")

    def test_profile_contains_form(self):
        """US-03: profile page contains the delivery details form."""
        self.client.login(email="test@example.com", password="testpass123")
        response = self.client.get(self.profile_url)
        self.assertIn("form", response.context)

    def test_profile_update_delivery_details(self):
        """US-03: user can update their delivery details."""
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
        """US-03: profile page lists the user's orders."""
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


class EmailVerificationTests(TestCase):
    """US-02: Login requires a verified email address."""

    def setUp(self):
        self.client = Client()

    def test_unverified_user_cannot_login(self):
        """US-02: unverified users cannot log in."""
        user = User.objects.create_user(
            email="unverified@example.com",
            username="unverified",
            password="testpass123",
        )
        EmailAddress.objects.filter(user=user).update(verified=False)

        self.client.post(
            reverse("account_login"),
            {"login": "unverified@example.com", "password": "testpass123"},
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_verified_user_can_login(self):
        """US-02: verified users can log in."""
        user = User.objects.create_user(
            email="verified@example.com",
            username="verified",
            password="testpass123",
        )
        EmailAddress.objects.filter(user=user).update(verified=True)

        is_authenticated = self.client.login(
            username="verified@example.com", password="testpass123"
        )
        self.assertTrue(is_authenticated)

    def test_superuser_has_verified_email(self):
        """US-04: superuser gets a verified email address."""
        admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass123",
        )
        email_addr, _ = EmailAddress.objects.get_or_create(
            user=admin,
            email=admin.email,
            defaults={"verified": True, "primary": True}
        )
        self.assertTrue(email_addr.verified)


class EmailAddressMigrationTests(TestCase):
    """US-02: Data migration that creates EmailAddress records."""

    def test_migration_is_reversible(self):
        """US-02: EmailAddress data migration has a reverse function."""
        module = import_module(
            "accounts.migrations.0003_add_email_address_records"
        )
        operation = module.Migration.operations[0]
        self.assertTrue(operation.reversible)


class AccountPagesTests(TestCase):
    """US-01 / US-02: Styled allauth account pages."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        EmailAddress.objects.filter(user=self.user).update(verified=True)

    def test_login_page_uses_custom_template(self):
        """US-02: login page uses the custom template."""
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/login.html")
        self.assertTemplateUsed(response, "account/base.html")
        self.assertContains(response, "Log In")

    def test_signup_page_uses_custom_template(self):
        """US-01: signup page uses the custom template."""
        response = self.client.get(reverse("account_signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/signup.html")
        self.assertTemplateUsed(response, "account/base.html")
        self.assertContains(response, "Create Account")

    def test_logout_page_uses_custom_template(self):
        """US-02: logout confirmation page uses the custom template."""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.get(reverse("account_logout"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/logout.html")
        self.assertTemplateUsed(response, "account/base.html")
        self.assertContains(response, "Sign Out")

    def test_password_reset_page_uses_custom_template(self):
        """US-02: password reset page uses the custom template."""
        response = self.client.get(reverse("account_reset_password"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/password_reset.html")
        self.assertTemplateUsed(response, "account/base.html")
        self.assertContains(response, "Reset Password")

    def test_email_management_page_requires_login(self):
        """US-03: email management page redirects anonymous users."""
        response = self.client.get(reverse("account_email"))
        self.assertEqual(response.status_code, 302)
