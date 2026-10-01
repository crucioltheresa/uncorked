import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.core import mail
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.template.loader import render_to_string
from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse
from django.views.defaults import permission_denied
from orders import pricing
from products.models import Region, Wine
from .models import ContactMessage, NewsletterSubscriber


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


class ValidHtmlTests(TestCase):
    """US-26: Markup fixes from the W3C HTML validator."""

    def setUp(self):
        self.client = Client()

    def test_homepage_has_no_c2pa_metadata(self):
        """US-26: the inlined world map has no C2PA metadata."""
        response = self.client.get(reverse("homepage"))
        self.assertNotContains(response, "c2pa")
        self.assertNotContains(response, "<metadata")
        self.assertContains(response, 'class="world-map"')

    def test_auth_modal_is_a_dialog(self):
        """US-01 / US-02: the login and signup modal has role="dialog"."""
        response = self.client.get(reverse("homepage"))
        self.assertContains(
            response,
            'id="authModal" tabindex="-1" role="dialog" aria-modal="true"',
        )

    def test_review_modal_is_a_dialog(self):
        """US-18: the review modal has role="dialog"."""
        html = render_to_string(
            "reviews/includes/review_modal.html", {"csrf_token": "token"}
        )
        self.assertIn(
            'id="reviewModal" tabindex="-1" role="dialog" aria-modal="true"',
            html,
        )

    def test_homepage_sections_have_headings(self):
        """US-26: the social proof and reviews sections have an h2."""
        response = self.client.get(reverse("homepage"))
        self.assertContains(
            response,
            '<h2 class="visually-hidden" id="socialProofTitle">'
            "Our philosophy and awards</h2>",
        )
        self.assertContains(
            response,
            '<h2 class="label label--heading" id="reviewsTitle">'
            "What People Say</h2>",
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
        """US-09: files are uploaded under the names the database uses."""
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


STATIC_PAGES = {
    "about": "core/about.html",
    "faq": "core/faq.html",
    "shipping_returns": "core/shipping_returns.html",
    "privacy": "core/privacy.html",
    "contact": "core/contact.html",
}


class StaticPagesTests(TestCase):
    """US-27: About, FAQ, Shipping & Returns, Privacy and Contact pages."""

    def setUp(self):
        self.client = Client()

    def test_each_page_loads_with_its_template(self):
        """US-27: every information page returns 200 with its template."""
        for name, template in STATIC_PAGES.items():
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertTemplateUsed(response, template)

    def test_footer_links_to_every_page(self):
        """US-27: the footer links to all the information pages."""
        response = self.client.get(reverse("homepage"))
        footer = response.content.decode().split('class="footer__links"')[1]
        footer = footer.split("</nav>")[0]
        for name in STATIC_PAGES:
            self.assertIn(f'href="{reverse(name)}"', footer)
        self.assertNotIn('href="#"', footer)

    def test_faq_uses_details_accordion(self):
        """US-27: FAQ answers are in an accessible <details> accordion."""
        response = self.client.get(reverse("faq"))
        self.assertContains(response, '<details class="faq__item">', count=7)
        for topic in ["18", "delivery take", "pay", "sommelier",
                      "damaged", "account"]:
            self.assertContains(response, topic)

    def test_privacy_mentions_stripe_deletion_and_email(self):
        """US-27: the privacy policy covers Stripe, deletion and contact."""
        response = self.client.get(reverse("privacy"))
        self.assertContains(response, "Stripe")
        self.assertContains(response, "delete")
        self.assertContains(response, "uncorked.store@gmail.com")


class ShippingPageTests(TestCase):
    """US-27: Shipping & Returns shows the real pricing rules."""

    def test_shows_values_from_pricing_module(self):
        """US-27: rates, threshold and discount come from orders.pricing."""
        response = self.client.get(reverse("shipping_returns"))
        self.assertContains(response, "€5.95")
        self.assertContains(response, "€9.95")
        self.assertContains(response, "€100 or more")
        self.assertContains(response, "10% off")
        self.assertContains(response, "Buy 8 bottles or more")
        self.assertContains(response, "across Ireland only")

    def test_follows_changes_to_pricing(self):
        """US-27: changing orders.pricing changes the page."""
        with (
            patch.object(pricing, "DUBLIN_DELIVERY_COST", Decimal("6.50")),
            patch.object(
                pricing, "FREE_DELIVERY_THRESHOLD", Decimal("120.00")
            ),
            patch.object(pricing, "BULK_DISCOUNT_MIN_BOTTLES", 12),
        ):
            response = self.client.get(reverse("shipping_returns"))
        self.assertContains(response, "€6.50")
        self.assertContains(response, "€120 or more")
        self.assertContains(response, "Buy 12 bottles or more")
        self.assertNotContains(response, "€5.95")


class ContactFormTests(TestCase):
    """US-27: Contact form saves messages and sends emails."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("contact")
        self.data = {
            "name": "Siobhán Kelly",
            "email": "siobhan@uncorked-mail.ie",
            "subject": "recommendation",
            "message": "Looking for a light red for a summer barbecue.",
            "website": "",
        }

    def test_valid_submission_saves_and_sends_emails(self):
        """US-27: a valid message is saved and emails store and sender."""
        response = self.client.post(self.url, self.data, follow=True)
        self.assertRedirects(response, self.url)
        self.assertContains(response, "Thanks for getting in touch!")
        message = ContactMessage.objects.get()
        self.assertEqual(message.subject, "recommendation")
        self.assertFalse(message.handled)

        self.assertEqual(len(mail.outbox), 2)
        store, sender = mail.outbox
        self.assertEqual(store.to, [settings.DEFAULT_FROM_EMAIL])
        self.assertEqual(store.reply_to, ["siobhan@uncorked-mail.ie"])
        self.assertIn("Wine recommendation", store.subject)
        self.assertIn("summer barbecue", store.body)
        self.assertEqual(sender.to, ["siobhan@uncorked-mail.ie"])
        self.assertIn("Hi Siobhán", sender.body)

    def test_invalid_email_shows_error(self):
        """US-27: an invalid email shows an error and nothing is saved."""
        response = self.client.post(
            self.url, dict(self.data, email="not-an-email")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a valid email address.")
        self.assertFalse(ContactMessage.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_fields_show_errors(self):
        """US-27: required fields show clear errors."""
        response = self.client.post(self.url, {"website": ""})
        self.assertContains(response, "Please tell us your name.")
        self.assertContains(
            response, "Please choose what your message is about."
        )
        self.assertContains(response, "Please write your message.")

    def test_honeypot_blocks_submission(self):
        """US-27: a filled honeypot is dropped: nothing saved or sent."""
        response = self.client.post(
            self.url, dict(self.data, website="http://spam.example"),
            follow=True,
        )
        self.assertContains(response, "Thanks for getting in touch!")
        self.assertFalse(ContactMessage.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_email_failure_is_logged_and_message_still_saved(self):
        """US-27: if sending fails, the message is kept and it's logged."""
        with patch(
            "core.views.EmailMessage.send", side_effect=OSError("SMTP down")
        ), self.assertLogs("core.views", level="ERROR") as logs:
            response = self.client.post(self.url, self.data)
        self.assertRedirects(response, self.url)
        self.assertTrue(ContactMessage.objects.exists())
        self.assertIn("Contact email", logs.output[0])

    def test_logged_in_user_gets_prefilled_fields(self):
        """US-27: name and email are pre-filled for logged-in users."""
        user = get_user_model().objects.create_user(
            email="member@uncorked-mail.ie", username="member", password="x"
        )
        user.profile.full_name = "Ciara Walsh"
        user.profile.save()
        self.client.force_login(user)
        response = self.client.get(self.url)
        form = response.context["form"]
        self.assertEqual(form.initial["name"], "Ciara Walsh")
        self.assertEqual(form.initial["email"], "member@uncorked-mail.ie")

    def test_messages_are_in_the_admin_with_filters(self):
        """US-27: the admin lists messages and filters by status and topic."""
        from django.contrib import admin
        model_admin = admin.site._registry[ContactMessage]
        self.assertIn("handled", model_admin.list_filter)
        self.assertIn("subject", model_admin.list_filter)


class SeoTests(TestCase):
    """US-22: robots.txt, sitemap, titles, descriptions and Open Graph."""

    def setUp(self):
        self.client = Client()
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Viña Sitemap", producer="Bodega Test", region=region,
            wine_type="red", abv=13.5, price="24.00", stock=5,
            character="Savoury and silky", tasting_notes="Dried cherry.",
            image="wines/image_1.jpg",
        )
        self.hidden = Wine.objects.create(
            name="Hidden Wine", producer="Bodega Test", region=region,
            wine_type="red", abv=13.5, price="24.00", stock=5,
            is_available=False,
        )

    def test_robots_txt(self):
        """US-22: robots.txt blocks private areas and points to the sitemap."""
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        content = response.content.decode()
        for path in ["/admin/", "/accounts/", "/cart/", "/checkout/",
                     "/webhook/", "/wines/add/", "/wines/*/edit/",
                     "/wines/*/delete/"]:
            self.assertIn(f"Disallow: {path}", content)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", content)

    def test_sitemap_lists_available_wines_only(self):
        """US-22: the sitemap includes available wines, not unavailable."""
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        content = response.content.decode()
        self.assertIn(reverse("wine_detail", args=[self.wine.slug]), content)
        hidden_url = reverse("wine_detail", args=[self.hidden.slug])
        self.assertNotIn(hidden_url, content)
        self.assertIn("<lastmod>", content)
        for name in ["about", "faq", "shipping_returns", "privacy", "contact"]:
            self.assertIn(reverse(name), content)

    def test_wine_page_has_own_title_description_and_image(self):
        """US-22: a wine page has its own title, description and og:image."""
        response = self.client.get(
            reverse("wine_detail", args=[self.wine.slug])
        )
        self.assertContains(response, "<title>Viña Sitemap — Uncorked</title>")
        self.assertContains(
            response,
            '<meta name="description" content="Viña Sitemap by Bodega Test',
        )
        self.assertContains(
            response,
            '<meta property="og:image" '
            'content="http://testserver/media/wines/image_1.jpg">',
        )
        self.assertContains(
            response,
            '<link rel="canonical" href="http://testserver'
            f'{reverse("wine_detail", args=[self.wine.slug])}">',
        )

    def test_pages_have_unique_titles_and_descriptions(self):
        """US-22: the main pages each have their own title and description."""
        titles, descriptions = set(), set()
        pages = ["homepage", "wine_list", "about", "faq",
                 "shipping_returns", "privacy", "contact", "account_login"]
        for name in pages:
            html = self.client.get(reverse(name)).content.decode()
            titles.add(html.split("<title>")[1].split("</title>")[0])
            descriptions.add(
                html.split('<meta name="description" content="')[1]
                .split('"')[0]
            )
        self.assertEqual(len(titles), len(pages))
        self.assertEqual(len(descriptions), len(pages))


class ErrorPageTests(TestCase):
    """Custom 404, 403 and 500 pages."""

    def test_missing_url_uses_custom_404(self):
        """US-26: a missing URL returns 404 with the custom page."""
        response = self.client.get("/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(
            response, "This bottle's gone missing", status_code=404
        )
        self.assertContains(response, reverse("wine_list"), status_code=404)

    def test_500_page_renders_without_context(self):
        """US-26: the 500 page renders with no request, context or database."""
        with self.assertNumQueries(0):
            html = render_to_string("500.html")
        self.assertIn("Something went wrong", html)
        self.assertIn('href="/wines/"', html)

    def test_403_page(self):
        """US-26: a permission error uses the custom 403 page."""
        request = RequestFactory().get("/")
        request.session = {}
        request.user = AnonymousUser()
        response = permission_denied(request, PermissionDenied())
        self.assertEqual(response.status_code, 403)
        html = response.content.decode()
        self.assertIn("staff only", html)
        self.assertIn(reverse("wine_list"), html)
