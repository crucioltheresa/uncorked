from django.test import TestCase, Client
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

    def test_signup_redirects_to_homepage(self):
        """US-23: newsletter signup redirects back to the homepage."""
        response = self.client.post(self.url, {"email": "new@example.com"})
        self.assertRedirects(response, reverse("homepage"))
