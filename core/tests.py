import tempfile
from io import StringIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, Client, override_settings
from django.urls import reverse
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
