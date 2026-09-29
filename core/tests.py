import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from orders import pricing
from .models import NewsletterSubscriber


class HomepageTests(TestCase):
    """US-26: Homepage."""

    def setUp(self):
        self.client = Client()

    def test_homepage_loads(self):
        """US-26: homepage returns 200 with the homepage template."""
        response = self.client.get(reverse("homepage"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/index.html")

    def test_pages_link_the_favicon(self):
        """US-26: every page links the SVG favicon and apple-touch-icon."""
        response = self.client.get(reverse("homepage"))
        self.assertContains(
            response,
            '<link rel="icon" href="/static/img/favicon.svg" '
            'type="image/svg+xml">',
            html=True,
        )
        self.assertContains(
            response,
            '<link rel="apple-touch-icon" '
            'href="/static/img/apple-touch-icon.png">',
            html=True,
        )

    def test_favicon_ico_redirects_to_svg(self):
        """US-26: /favicon.ico no longer 404s; it points to the SVG icon."""
        response = self.client.get("/favicon.ico")
        self.assertRedirects(
            response, "/static/img/favicon.svg", fetch_redirect_response=False
        )


class NewsletterSignupTests(TestCase):
    """US-23: Newsletter signup."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("newsletter_signup")
        NewsletterSubscriber.objects.create(email="existing@example.com")

    def test_valid_email_creates_subscriber(self):
        """US-23: valid email creates a subscriber and thanks the user."""
        response = self.client.post(
            self.url, {"email": "new@example.com"}, follow=True
        )
        subscribers = NewsletterSubscriber.objects.filter(
            email="new@example.com"
        )
        self.assertTrue(subscribers.exists())
        self.assertContains(response, "Thanks for subscribing!")

    def test_duplicate_email_shows_info_message(self):
        """US-23: duplicate email shows an info message, adds no subscriber."""
        response = self.client.post(
            self.url, {"email": "existing@example.com"}, follow=True
        )
        subscribers = NewsletterSubscriber.objects.filter(
            email="existing@example.com"
        )
        self.assertEqual(subscribers.count(), 1)
        self.assertContains(response, "already subscribed")

    def test_invalid_email_shows_error(self):
        """US-23: invalid email shows an error and is not saved."""
        response = self.client.post(
            self.url, {"email": "notanemail"}, follow=True
        )
        self.assertFalse(
            NewsletterSubscriber.objects.filter(email="notanemail").exists()
        )
        self.assertContains(response, "Please enter a valid email address.")

    def test_signup_redirects_to_homepage(self):
        """US-23: newsletter signup redirects back to the homepage."""
        response = self.client.post(self.url, {"email": "new@example.com"})
        self.assertRedirects(response, reverse("homepage"))


IN_MEMORY_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


class UploadMediaCommandTests(TestCase):
    """US-09: One-off upload of local media to the default storage."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.media_root = Path(temp_dir.name)
        (self.media_root / "wines").mkdir()
        (self.media_root / "wines" / "image_3.jpg").write_bytes(b"new")

    def test_uploads_files_with_same_names(self):
        """US-09: files are uploaded under the exact names the database uses."""
        with override_settings(
            STORAGES=IN_MEMORY_STORAGES, MEDIA_ROOT=self.media_root
        ):
            call_command("upload_media", stdout=StringIO())
            with default_storage.open("wines/image_3.jpg") as uploaded:
                self.assertEqual(uploaded.read(), b"new")

    def test_existing_file_is_overwritten_not_renamed(self):
        """US-09: an existing file is replaced under the same name."""
        with override_settings(
            STORAGES=IN_MEMORY_STORAGES, MEDIA_ROOT=self.media_root
        ):
            default_storage.save("wines/image_3.jpg", ContentFile(b"old"))
            call_command("upload_media", stdout=StringIO())
            _, files = default_storage.listdir("wines")
            self.assertEqual(files, ["image_3.jpg"])
            with default_storage.open("wines/image_3.jpg") as uploaded:
                self.assertEqual(uploaded.read(), b"new")

    def test_refuses_to_run_on_local_storage(self):
        """US-09: the command stops if media is still the local folder."""
        local_storages = dict(
            IN_MEMORY_STORAGES,
            default={
                "BACKEND": "django.core.files.storage.FileSystemStorage"
            },
        )
        with override_settings(
            STORAGES=local_storages, MEDIA_ROOT=self.media_root
        ):
            with self.assertRaises(CommandError):
                call_command("upload_media", stdout=StringIO())


class PromoBarTests(TestCase):
    """US-26: The promo bar reads its values from the pricing rules."""

    def setUp(self):
        self.client = Client()

    def test_promo_bar_shows_current_pricing(self):
        """US-26: the promo bar shows the discount and free delivery rules."""
        response = self.client.get(reverse("homepage"))
        self.assertContains(
            response, "10% off if you buy 8 Bottles Of Wine or More!"
        )
        self.assertContains(
            response, "Free National Delivery on orders of €100+"
        )

    def test_promo_bar_follows_changes_to_pricing(self):
        """US-26: changing orders.pricing changes the promo text."""
        with patch.object(pricing, "BULK_DISCOUNT_RATE", Decimal("0.15")), \
                patch.object(pricing, "BULK_DISCOUNT_MIN_BOTTLES", 6), \
                patch.object(
                    pricing, "FREE_DELIVERY_THRESHOLD", Decimal("80.50")
                ):
            response = self.client.get(reverse("homepage"))
        self.assertContains(
            response, "15% off if you buy 6 Bottles Of Wine or More!"
        )
        self.assertContains(
            response, "Free National Delivery on orders of €80.50+"
        )
        self.assertNotContains(response, "10% off")

    def test_messages_are_passed_to_the_slider_script(self):
        """US-26: the rotating promo gets its messages as JSON, not from JS."""
        response = self.client.get(reverse("homepage"))
        self.assertContains(response, '<script id="promoMessages"')
        self.assertEqual(
            response.context["promo_messages"],
            [
                "10% off if you buy 8 Bottles Of Wine or More!",
                "Free National Delivery on orders of €100+",
            ],
        )
