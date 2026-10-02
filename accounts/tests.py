from importlib import import_module

from django.apps import apps
from django.contrib import admin
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.core.cache import cache
from allauth.account.models import EmailAddress
from django.contrib.sites.models import Site
from .models import UserProfile
from core.models import ContactMessage, NewsletterSubscriber
from orders.models import Order, OrderItem
from products.models import Wine, Region
from reviews.models import Review
from wishlist.models import WishlistItem

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
        """US-01: valid signup creates a user and asks to confirm email."""
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
        """US-01: duplicate email creates no account and tells the owner."""
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
        self.client.login(
            username="test@example.com", password="Str0ngPass!23"
        )
        response = self.client.get(reverse("account_login"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_logged_in_user_redirected_from_signup_page(self):
        """US-01: logged-in user cannot access or post the signup page."""
        self.client.login(
            username="test@example.com", password="Str0ngPass!23"
        )
        response = self.client.get(reverse("account_signup"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)

        response = self.client.post(reverse("account_signup"), {
            "email": "second@example.com",
            "password1": "Str0ngPass!23",
            "password2": "Str0ngPass!23",
        })
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertFalse(
            User.objects.filter(email="second@example.com").exists()
        )

    def test_logout_logs_user_out(self):
        """US-02: logout ends the session and redirects home."""
        self.client.login(
            username="test@example.com", password="Str0ngPass!23"
        )
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
        self.assertEqual(
            str(self.user.profile), f"Profile for {self.user.email}"
        )


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
                "city": "Dublin",
                "postcode": "D02 X285",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.full_name, "John Doe")
        self.assertEqual(self.user.profile.city, "Dublin")

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
            grand_total=10.00,
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


class ProfileEircodeTests(TestCase):
    """US-03: Profile delivery details use an Eircode, Ireland only."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.client.force_login(self.user)
        self.url = reverse("profile")
        self.data = {
            "full_name": "Aoife Byrne",
            "email": "aoife@example.com",
            "address_line1": "1 Patrick Street",
            "address_line2": "",
            "city": "Cork",
            "postcode": "T12 X70A",
        }

    def test_valid_eircode_is_saved_normalised(self):
        """US-03: a lowercase Eircode without a space is saved normalised."""
        self.client.post(self.url, dict(self.data, postcode="t12x70a"))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.postcode, "T12 X70A")

    def test_invalid_eircode_shows_error_and_is_not_saved(self):
        """US-03: an invalid Eircode shows an error and nothing is saved."""
        response = self.client.post(
            self.url, dict(self.data, postcode="10001")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a valid Eircode")
        self.user.profile.refresh_from_db()
        self.assertNotEqual(self.user.profile.postcode, "10001")
        self.assertNotEqual(self.user.profile.city, "Cork")

    def test_country_is_always_ireland(self):
        """US-03: a posted country is ignored; the profile is Ireland."""
        self.client.post(self.url, dict(self.data, country="USA"))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.country, "Ireland")

    def test_eircode_can_be_left_empty(self):
        """US-03: the Eircode is optional on the profile."""
        response = self.client.post(self.url, dict(self.data, postcode=""))
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.postcode, "")

    def test_page_shows_eircode_and_fixed_country(self):
        """US-03: the form asks for an Eircode and shows Ireland as fixed."""
        response = self.client.get(self.url)
        self.assertContains(response, 'placeholder="Eircode"')
        self.assertContains(response, "Country: Ireland")
        self.assertNotContains(response, 'name="country"')


class SiteNameTests(TestCase):
    """US-01: The site is named Uncorked, never example.com."""

    def test_default_site_is_uncorked(self):
        """US-01: the data migration names the default site Uncorked."""
        site = Site.objects.get_current()
        self.assertEqual(site.name, "Uncorked")
        self.assertEqual(
            site.domain, "uncorked-store-5dff5e1aa357.herokuapp.com"
        )


class SignupConfirmationEmailTests(TestCase):
    """US-01: The signup confirmation email is branded and has the link."""

    def setUp(self):
        # allauth rate-limits emails per address; limits live in the cache
        cache.clear()
        self.client = Client()
        self.client.post(reverse("account_signup"), {
            "email": "maeve.quill@uncorked-mail.ie",
            "password1": "Str0ngPass!23",
            "password2": "Str0ngPass!23",
        })
        self.user = User.objects.get(email="maeve.quill@uncorked-mail.ie")
        self.email = mail.outbox[0]
        self.html = self.email.alternatives[0][0]

    def test_subject_and_text(self):
        """US-01: the email has the Uncorked subject and welcome text."""
        self.assertEqual(
            self.email.subject,
            "Welcome to Uncorked! Please confirm your email",
        )
        self.assertIn("Welcome to Uncorked!", self.email.body)
        self.assertIn("The Uncorked Team", self.email.body)
        self.assertIn("expires in 3 days", self.email.body)

    def test_contains_confirmation_link(self):
        """US-01: text and HTML versions both contain the confirm link."""
        confirm_url = reverse("account_confirm_email", args=["x"])[:-2]
        link = f"http://testserver{confirm_url}"
        self.assertIn(link, self.email.body)
        self.assertIn(link, self.html)

    def test_no_example_com_or_username(self):
        """US-01: the email never shows example.com or the username."""
        self.assertTrue(self.user.username)
        for content in [self.email.subject, self.email.body, self.html]:
            self.assertNotIn("example.com", content)
            self.assertNotIn(self.user.username, content)

    def test_duplicate_signup_email_is_branded(self):
        """US-01: duplicate signup gets the branded "already exists" email."""
        mail.outbox.clear()
        # Same address again: reset the per-address email rate limit
        cache.clear()
        self.client.post(reverse("account_signup"), {
            "email": "maeve.quill@uncorked-mail.ie",
            "password1": "Str0ngPass!23",
            "password2": "Str0ngPass!23",
        })
        email = mail.outbox[0]
        self.assertEqual(email.subject, "You already have an Uncorked account")
        self.assertIn("/accounts/password/reset/", email.body)
        self.assertNotIn("example.com", email.body)
        # The address itself is shown; the username must not appear elsewhere
        body = email.body.replace("maeve.quill@uncorked-mail.ie", "")
        self.assertNotIn(self.user.username, body)


class PasswordResetEmailTests(TestCase):
    """US-02: The password reset email is branded and has the link."""

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            email="reset@uncorked-mail.ie",
            username="auto-user-7731",
            password="Str0ngPass!23",
        )
        EmailAddress.objects.filter(user=self.user).update(verified=True)

    def request_reset(self):
        self.client.post(
            reverse("account_reset_password"),
            {"email": "reset@uncorked-mail.ie"},
        )
        return mail.outbox[0]

    def test_subject_text_and_link(self):
        """US-02: Uncorked subject, friendly text and the reset link."""
        email = self.request_reset()
        self.assertEqual(email.subject, "Reset your Uncorked password")
        self.assertIn("Hi there,", email.body)
        self.assertIn(
            "reset the password for your Uncorked account", email.body
        )
        self.assertIn(
            "http://testserver/accounts/password/reset/key/", email.body
        )
        self.assertIn(
            "http://testserver/accounts/password/reset/key/",
            email.alternatives[0][0],
        )
        self.assertIn("expires in 3 days", email.body)

    def test_no_example_com_or_username(self):
        """US-02: the reset email never shows example.com or the username."""
        email = self.request_reset()
        for content in [email.subject, email.body, email.alternatives[0][0]]:
            self.assertNotIn("example.com", content)
            self.assertNotIn("auto-user-7731", content)

    def test_greets_by_first_name_when_known(self):
        """US-02: the email greets the user by first name if there is one."""
        self.user.first_name = "Aoife"
        self.user.save()
        email = self.request_reset()
        self.assertIn("Hi Aoife,", email.body)


AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class AuthModalTests(TestCase):
    """US-01 / US-02: Login and signup in a modal."""

    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            email="modal@uncorked-mail.ie",
            username="modaluser",
            password="Str0ngPass!23",
        )
        # create_user makes no allauth EmailAddress; login needs a verified one
        EmailAddress.objects.update_or_create(
            user=self.user,
            email=self.user.email,
            defaults={"verified": True, "primary": True},
        )

    def test_modal_markup_for_logged_out_users(self):
        """US-01: logged-out pages include the modal and its script."""
        response = self.client.get(reverse("wine_list"))
        self.assertContains(response, 'id="authModal"')
        self.assertContains(response, 'data-auth-form="login"')
        self.assertContains(response, 'data-auth-form="signup"')
        self.assertContains(response, "js/auth_modal.js")
        self.assertContains(
            response,
            f'<a href="{reverse("account_login")}" class="nav__icon" '
            'title="Log in or sign up" aria-label="Log in or sign up" '
            'data-auth-open="login">',
        )
        self.assertContains(
            response, 'aria-describedby="signup-password2-error"'
        )

    def test_no_modal_for_logged_in_users(self):
        """US-02: logged-in pages don't include the modal."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("wine_list"))
        self.assertNotContains(response, 'id="authModal"')
        self.assertNotContains(response, "js/auth_modal.js")

    def test_login_fetch_success_returns_location(self):
        """US-02: a fetch login returns JSON with where to go next."""
        response = self.client.post(reverse("account_login"), {
            "login": "modal@uncorked-mail.ie",
            "password": "Str0ngPass!23",
            "next": "/wines/",
        }, **AJAX)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["location"], "/wines/")
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_fetch_error_returns_form_errors(self):
        """US-02: a wrong password returns 400 with the error message."""
        response = self.client.post(reverse("account_login"), {
            "login": "modal@uncorked-mail.ie",
            "password": "WrongPass!99",
        }, **AJAX)
        self.assertEqual(response.status_code, 400)
        errors = response.json()["form"]["errors"]
        self.assertIn(
            "The email address and/or password you specified are not correct.",
            errors,
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_signup_fetch_success_points_to_verification(self):
        """US-01: a fetch signup goes to "check your email" (verification)."""
        response = self.client.post(reverse("account_signup"), {
            "email": "newmodal@uncorked-mail.ie",
            "password1": "Str0ngPass!23",
            "password2": "Str0ngPass!23",
        }, **AJAX)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["location"],
            reverse("account_email_verification_sent"),
        )
        self.assertTrue(
            User.objects.filter(email="newmodal@uncorked-mail.ie").exists()
        )

    def test_signup_fetch_error_returns_field_errors(self):
        """US-01: mismatched passwords return 400 with the field error."""
        response = self.client.post(reverse("account_signup"), {
            "email": "newmodal@uncorked-mail.ie",
            "password1": "Str0ngPass!23",
            "password2": "Different!456",
        }, **AJAX)
        self.assertEqual(response.status_code, 400)
        fields = response.json()["form"]["fields"]
        self.assertIn(
            "You must type the same password each time.",
            fields["password2"]["errors"],
        )
        self.assertFalse(
            User.objects.filter(email="newmodal@uncorked-mail.ie").exists()
        )

    def test_full_pages_still_work(self):
        """US-01 / US-02: the full login and signup pages still work."""
        self.assertTemplateUsed(
            self.client.get(reverse("account_login")), "account/login.html"
        )
        self.assertTemplateUsed(
            self.client.get(reverse("account_signup")), "account/signup.html"
        )
        response = self.client.post(reverse("account_login"), {
            "login": "modal@uncorked-mail.ie",
            "password": "Str0ngPass!23",
        })
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_message_does_not_show_username(self):
        """US-02: the welcome message doesn't show the generated username."""
        response = self.client.post(reverse("account_login"), {
            "login": "modal@uncorked-mail.ie",
            "password": "Str0ngPass!23",
        }, follow=True)
        self.assertContains(response, "Welcome back! You&#x27;re logged in.")
        self.assertNotContains(response, "modaluser")

    def test_logout_post_logs_out_and_redirects_home(self):
        """US-02: logging out by POST ends the session and goes home."""
        self.client.force_login(self.user)
        response = self.client.post(reverse("account_logout"), follow=True)
        self.assertRedirects(response, "/")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "You&#x27;ve logged out. See you soon!")

    def test_profile_logout_is_a_post_form(self):
        """US-02: the profile's log out option is a POST form, not a link."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("profile"))
        self.assertContains(
            response,
            f'<form method="POST" action="{reverse("account_logout")}" '
            'class="profile__logout">',
        )
        self.assertNotContains(
            response, f'<a href="{reverse("account_logout")}"'
        )


class AdminPanelTests(TestCase):
    """US-04: Every model is manageable in the admin panel."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            email="boss@uncorked-mail.ie",
            username="boss",
            password="adminpass123",
        )
        self.client.force_login(self.admin)
        # One row of each model, so every changelist renders real rows
        region = Region.objects.create(name="Rioja", country="Spain")
        wine = Wine.objects.create(
            name="Admin Red", producer="Test", region=region,
            wine_type="red", abv=13.5, price="20.00", stock=5,
        )
        order = Order.objects.create(
            user=self.admin, full_name="Boss", email="boss@uncorked-mail.ie",
            address_line1="1 Main St", city="Dublin", postcode="D02 X285",
            country="Ireland", grand_total="20.00", status="paid",
        )
        OrderItem.objects.create(
            order=order, wine=wine, quantity=1, price_at_purchase="20.00"
        )
        self.review = Review.objects.create(
            wine=wine, user=self.admin, rating=5, title="Great",
            body="Lovely wine.", verified_purchase=True,
        )
        WishlistItem.objects.create(user=self.admin, wine=wine)
        NewsletterSubscriber.objects.create(email="news@uncorked-mail.ie")
        ContactMessage.objects.create(
            name="Aoife", email="aoife@uncorked-mail.ie", subject="other",
            message="Just saying hello to the team.",
        )

    def test_every_changelist_loads_for_superuser(self):
        """US-04: each registered admin changelist returns 200."""
        for model in admin.site._registry:
            meta = model._meta
            url = reverse(
                f"admin:{meta.app_label}_{meta.model_name}_changelist"
            )
            with self.subTest(model=meta.label):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_project_models_are_all_registered(self):
        """US-04: every model in the project's apps is in the admin."""
        project_apps = {
            "accounts", "core", "products", "orders", "reviews", "wishlist",
        }
        for model in apps.get_models():
            if model._meta.app_label in project_apps:
                with self.subTest(model=model._meta.label):
                    self.assertTrue(admin.site.is_registered(model))

    def test_staff_can_delete_a_review(self):
        """US-04: staff can delete a review from the admin."""
        url = reverse("admin:reviews_review_delete", args=[self.review.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {"post": "yes"})
        self.assertRedirects(
            response, reverse("admin:reviews_review_changelist")
        )
        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())

    def test_reviews_changelist_filters_by_rating_and_verified(self):
        """US-04: reviews can be filtered by rating and verified purchase."""
        url = reverse("admin:reviews_review_changelist")
        response = self.client.get(
            url, {"rating": 5, "verified_purchase__exact": 1}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Red")

    def test_add_user_page_uses_custom_user_model(self):
        """US-04: staff can add a user (email-based custom user model)."""
        url = reverse("admin:accounts_customuser_add")
        self.assertContains(self.client.get(url), 'name="email"')
        response = self.client.post(url, {
            "email": "newstaff@uncorked-mail.ie",
            "username": "newstaff",
            "usable_password": "true",
            "password1": "Str0ngPass!23",
            "password2": "Str0ngPass!23",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            User.objects.filter(email="newstaff@uncorked-mail.ie").exists()
        )

    def test_user_change_page_shows_profile(self):
        """US-04: a user's admin page includes their delivery details."""
        url = reverse(
            "admin:accounts_customuser_change", args=[self.admin.pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profile-0-full_name")


class AccountAreaByRoleTests(TestCase):
    """US-03 / US-04: The account area depends on the user's role."""

    def setUp(self):
        self.client = Client()
        self.customer = User.objects.create_user(
            email="shopper@example.com", username="shopper", password="x"
        )
        self.manager = User.objects.create_user(
            email="manager@example.com", username="manager", password="x"
        )
        self.manager.groups.add(Group.objects.get(name="Store Manager"))
        self.admin = User.objects.create_superuser(
            email="dev@example.com", username="dev", password="x"
        )
        self.dashboard_url = reverse("dashboard:overview")
        self.profile_url = reverse("profile")

    def nav_account_link(self, response):
        """The href of the nav account icon (the person icon)."""
        html = response.content.decode()
        icon = html.index('<i class="bi bi-person-fill"')
        start = html.rindex('<a href="', 0, icon) + len('<a href="')
        return html[start:html.index('"', start)]

    def test_store_manager_profile_redirects_to_dashboard(self):
        """US-04: a store manager's profile page is the dashboard."""
        self.client.force_login(self.manager)
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, self.dashboard_url)

    def test_store_manager_nav_icon_points_to_dashboard(self):
        """US-04: a store manager's account icon opens the dashboard."""
        self.client.force_login(self.manager)
        response = self.client.get(reverse("wine_list"))
        self.assertEqual(self.nav_account_link(response), self.dashboard_url)

    def test_superuser_keeps_profile_with_dashboard_button(self):
        """US-04: a superuser keeps the profile, with a dashboard button."""
        self.client.force_login(self.admin)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertContains(response, f'href="{self.dashboard_url}"')
        self.assertEqual(self.nav_account_link(response), self.profile_url)

    def test_customer_keeps_profile(self):
        """US-03: a customer's account icon and profile are unchanged."""
        self.client.force_login(self.customer)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.nav_account_link(response), self.profile_url)
        self.assertNotContains(response, f'href="{self.dashboard_url}"')


class ProfileReviewsTests(TestCase):
    """US-03 / US-18 / US-19: "My Reviews" on the profile."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="critic@example.com", username="critic", password="x"
        )
        region = Region.objects.create(name="Rioja", country="Spain")
        self.old_wine = Wine.objects.create(
            name="Older Red", producer="Test", region=region,
            wine_type="red", abv=13, price="15.00", stock=5,
        )
        self.new_wine = Wine.objects.create(
            name="Newer White", producer="Test", region=region,
            wine_type="white", abv=12, price="15.00", stock=5,
        )
        self.client.force_login(self.user)

    def add_reviews(self):
        older = Review.objects.create(
            wine=self.old_wine, user=self.user, rating=3, title="Decent",
            body="Fine on a Tuesday.",
        )
        newer = Review.objects.create(
            wine=self.new_wine, user=self.user, rating=5, title="Superb",
            body="Bright and crisp.", verified_purchase=True,
        )
        return older, newer

    def test_lists_reviews_newest_first_with_details(self):
        """US-03: My Reviews shows each review, newest first."""
        older, newer = self.add_reviews()
        response = self.client.get(reverse("profile"))
        self.assertEqual(list(response.context["reviews"]), [newer, older])
        self.assertContains(response, "My Reviews")
        self.assertContains(response, "Superb")
        self.assertContains(response, "Bright and crisp.")
        self.assertContains(
            response, reverse("wine_detail", args=[self.new_wine.slug])
        )
        self.assertContains(response, 'aria-label="5 out of 5 stars"')
        self.assertContains(response, "Verified purchase")

    def test_each_review_has_edit_and_delete(self):
        """US-18 / US-19: edit uses the review modal; delete confirms."""
        older, newer = self.add_reviews()
        response = self.client.get(reverse("profile"))
        profile_path = reverse("profile")
        for review in [older, newer]:
            edit_url = reverse("edit_review", args=[review.id])
            delete_url = reverse("delete_review", args=[review.id])
            self.assertContains(response, f'data-url="{edit_url}"')
            self.assertContains(
                response, f'href="{delete_url}?next={profile_path}"'
            )
        self.assertContains(response, 'id="reviewModal"')
        self.assertContains(response, "js/reviews_modal.js")

    def test_empty_state(self):
        """US-03: no reviews yet shows a friendly message and a link."""
        response = self.client.get(reverse("profile"))
        self.assertContains(response, "You haven't reviewed any wines yet.")
        self.assertContains(response, reverse("wine_list"))
        self.assertNotContains(response, 'id="reviewModal"')

    def test_profile_layout_classes(self):
        """US-03: details and order history are laid out as two columns."""
        response = self.client.get(reverse("profile"))
        self.assertContains(response, "profile__section--details")
        self.assertContains(response, "profile__section--orders")
