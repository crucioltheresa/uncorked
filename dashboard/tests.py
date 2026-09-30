from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core.decorators import DASHBOARD_PERMISSION
from core.models import ContactMessage
from orders.models import Order
from products.models import Region, Wine
from reviews.models import Review

User = get_user_model()


def make_order(status, total, email="buyer@example.com", days_ago=0):
    """Create an order; created_at is set afterwards (it's auto_now_add)."""
    order = Order.objects.create(
        full_name="Buyer", email=email, address_line1="1 Main St",
        city="Dublin", postcode="D02 X285", country="Ireland",
        subtotal=Decimal(total), grand_total=Decimal(total), status=status,
    )
    if days_ago:
        Order.objects.filter(pk=order.pk).update(
            created_at=timezone.now() - timedelta(days=days_ago)
        )
    return order


class DashboardTestCase(TestCase):
    """Shared set-up: a superuser, a customer and a region."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            email="owner@example.com", username="owner", password="x"
        )
        self.customer = User.objects.create_user(
            email="customer@example.com", username="customer", password="x"
        )
        self.region = Region.objects.create(name="Rioja", country="Spain")

    def wine(self, name, **fields):
        values = {
            "producer": "Bodega Test", "region": self.region,
            "wine_type": "red", "abv": 13, "price": "15.00", "stock": 10,
        }
        values.update(fields)
        return Wine.objects.create(name=name, **values)

    def dashboard_urls(self):
        wine = self.wine("Access Red")
        order = make_order("paid", "20.00")
        message = ContactMessage.objects.create(
            name="A", email="a@example.com", subject="other",
            message="Hello there, just a question.",
        )
        review = Review.objects.create(
            wine=wine, user=self.customer, rating=4, title="Nice", body="Ok"
        )
        return [
            ("get", reverse("dashboard:overview")),
            ("get", reverse("dashboard:wines")),
            ("post", reverse("dashboard:wine_toggle_available",
                             args=[wine.id])),
            ("get", reverse("dashboard:orders")),
            ("get", reverse("dashboard:order_detail",
                            args=[order.order_number])),
            ("post", reverse("dashboard:order_status",
                             args=[order.order_number])),
            ("get", reverse("dashboard:messages")),
            ("get", reverse("dashboard:message_detail", args=[message.pk])),
            ("post", reverse("dashboard:message_handled",
                             args=[message.pk])),
            ("get", reverse("dashboard:reviews")),
            ("get", reverse("dashboard:review_delete", args=[review.pk])),
            ("post", reverse("dashboard:review_delete", args=[review.pk])),
            ("get", reverse("dashboard:regions")),
            ("get", reverse("dashboard:region_add")),
            ("get", reverse("dashboard:region_edit",
                            args=[self.region.pk])),
        ]


class DashboardAccessTests(DashboardTestCase):
    """US-09 / US-15: Only superusers can use the Store Dashboard."""

    def test_logged_out_users_are_sent_to_login(self):
        """US-09: logged-out visitors are redirected to login everywhere."""
        for method, url in self.dashboard_urls():
            with self.subTest(url=url):
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_customers_are_refused_with_a_message(self):
        """US-09: logged-in non-superusers are refused with an error."""
        self.client.force_login(self.customer)
        for method, url in self.dashboard_urls():
            with self.subTest(url=url):
                response = getattr(self.client, method)(url)
                self.assertRedirects(
                    response, reverse("wine_list"),
                    fetch_redirect_response=False,
                )
        response = self.client.get(reverse("dashboard:overview"), follow=True)
        self.assertContains(response, "Only site administrators")
        self.assertEqual(Review.objects.count(), 1)
        self.assertFalse(ContactMessage.objects.get().handled)

    def test_superuser_can_open_every_page(self):
        """US-09: a superuser can open every dashboard page."""
        self.client.force_login(self.admin)
        for method, url in self.dashboard_urls():
            if method == "get":
                with self.subTest(url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_dashboard_link_only_for_superusers(self):
        """US-09: the superuser's profile links to the dashboard."""
        link = f'href="{reverse("dashboard:overview")}"'
        self.client.force_login(self.customer)
        self.assertNotContains(self.client.get(reverse("profile")), link)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("profile"))
        self.assertContains(response, link)
        self.assertContains(response, "Store Dashboard")


class OverviewTests(DashboardTestCase):
    """US-09 / US-15: Overview numbers for a small known dataset."""

    def setUp(self):
        super().setUp()
        # Paid-type orders: last 30 days = 50 + 30; all time adds 20 + 15
        make_order("paid", "50.00")
        make_order("shipped", "30.00")
        make_order("paid", "20.00", days_ago=40)
        make_order("delivered", "15.00", days_ago=60)
        # Not counted as sales
        make_order("pending", "99.00")
        make_order("cancelled", "10.00")
        # Stock: two low (3 and 5), one fine (6), one out; hidden ignored
        self.wine("Low A", stock=3)
        self.wine("Low B", stock=5)
        self.wine("Fine", stock=6)
        self.wine("Empty", stock=0)
        self.wine("Hidden Empty", stock=0, is_available=False)
        for handled in [False, False, True]:
            ContactMessage.objects.create(
                name="N", email="n@example.com", subject="other",
                message="A message long enough.", handled=handled,
            )
        wine = Wine.objects.get(name="Fine")
        for i in range(6):
            Review.objects.create(
                wine=wine, user=User.objects.create_user(
                    email=f"r{i}@example.com", username=f"r{i}",
                    password="x",
                ),
                rating=5, title=f"Review {i}", body="Good",
            )
        self.client.force_login(self.admin)

    def test_overview_numbers(self):
        """US-15: sales, orders to ship, stock and messages are correct."""
        context = self.client.get(reverse("dashboard:overview")).context
        self.assertEqual(context["sales_30_days"]["count"], 2)
        self.assertEqual(context["sales_30_days"]["revenue"], Decimal("80"))
        self.assertEqual(context["sales_all_time"]["count"], 4)
        self.assertEqual(
            context["sales_all_time"]["revenue"], Decimal("115")
        )
        self.assertEqual(context["to_ship_count"], 2)
        self.assertEqual(context["low_stock_count"], 2)
        self.assertEqual(context["out_of_stock_count"], 1)
        self.assertEqual(context["unhandled_count"], 2)
        self.assertEqual(len(context["latest_reviews"]), 5)

    def test_overview_shows_values_and_links(self):
        """US-15: the cards show the figures and link to their sections."""
        response = self.client.get(reverse("dashboard:overview"))
        self.assertContains(response, "€80.00 revenue")
        self.assertContains(response, "€115.00 revenue")
        self.assertContains(
            response, f'href="{reverse("dashboard:orders")}?status=paid"'
        )
        self.assertContains(
            response,
            f'href="{reverse("dashboard:messages")}?handled=no"',
        )
        self.assertContains(response, "Review 5")


class WinesSectionTests(DashboardTestCase):
    """US-09: Wines list, search, filters and availability toggle."""

    def setUp(self):
        super().setUp()
        self.red = self.wine("Tondonia", producer="López de Heredia")
        self.white = self.wine(
            "Albariño Mar", producer="Bodega Mar", wine_type="white",
            stock=2,
        )
        self.hidden = self.wine("Old Rosé", wine_type="rose",
                                is_available=False)
        self.url = reverse("dashboard:wines")
        self.client.force_login(self.admin)

    def names(self, **params):
        response = self.client.get(self.url, params)
        return [wine.name for wine in response.context["page"]]

    def test_lists_all_wines_including_hidden(self):
        """US-09: the list shows every wine, available or not."""
        self.assertEqual(
            self.names(), ["Albariño Mar", "Old Rosé", "Tondonia"]
        )

    def test_search_by_name_and_producer(self):
        """US-09: search matches wine name or producer."""
        self.assertEqual(self.names(q="tondo"), ["Tondonia"])
        self.assertEqual(self.names(q="heredia"), ["Tondonia"])

    def test_filters(self):
        """US-09: filter by type, availability and low stock."""
        self.assertEqual(self.names(type="white"), ["Albariño Mar"])
        self.assertEqual(self.names(available="no"), ["Old Rosé"])
        self.assertEqual(self.names(stock="low"), ["Albariño Mar"])
        self.assertEqual(self.names(type="beer"), self.names())

    def test_toggle_available(self):
        """US-09: the toggle hides and shows a wine (POST)."""
        url = reverse("dashboard:wine_toggle_available", args=[self.red.id])
        response = self.client.post(url, {"next": f"{self.url}?q=tondo"})
        self.assertRedirects(response, f"{self.url}?q=tondo")
        self.red.refresh_from_db()
        self.assertFalse(self.red.is_available)
        self.client.post(url)
        self.red.refresh_from_db()
        self.assertTrue(self.red.is_available)

    def test_toggle_requires_post_and_ignores_outside_next(self):
        """US-09: GET is refused; "next" can't leave the dashboard."""
        url = reverse("dashboard:wine_toggle_available", args=[self.red.id])
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url, {"next": "https://evil.example/"})
        self.assertRedirects(response, self.url)

    def test_links_to_product_management(self):
        """US-09: the list links to the existing add, edit and delete."""
        response = self.client.get(self.url)
        self.assertContains(response, reverse("wine_add"))
        self.assertContains(response, reverse("wine_edit",
                                              args=[self.red.slug]))
        self.assertContains(response, reverse("wine_delete",
                                              args=[self.red.slug]))


class OrdersSectionTests(DashboardTestCase):
    """US-15: Orders list, filters, detail and status changes."""

    def setUp(self):
        super().setUp()
        self.paid = make_order("paid", "42.00", email="aoife@example.com")
        self.shipped = make_order("shipped", "18.00", email="sean@example.com")
        self.client.force_login(self.admin)

    def emails(self, **params):
        response = self.client.get(reverse("dashboard:orders"), params)
        return [order.email for order in response.context["page"]]

    def test_filter_by_status(self):
        """US-15: orders can be filtered by status."""
        self.assertEqual(self.emails(status="shipped"), ["sean@example.com"])
        self.assertEqual(len(self.emails()), 2)

    def test_search_by_email_and_order_number(self):
        """US-15: search by email or the short order number."""
        self.assertEqual(self.emails(q="aoife"), ["aoife@example.com"])
        short = str(self.paid.order_number)[:8].upper()
        self.assertEqual(self.emails(q=short), ["aoife@example.com"])

    def test_detail_shows_items_totals_and_eircode(self):
        """US-15: the order page shows totals and delivery with Eircode."""
        response = self.client.get(
            reverse("dashboard:order_detail",
                    args=[self.paid.order_number])
        )
        self.assertContains(response, "D02 X285")
        self.assertContains(response, "€42.00")
        self.assertContains(response, 'value="delivered"')

    def test_status_change(self):
        """US-15: staff can change an order's status by POST."""
        url = reverse("dashboard:order_status",
                      args=[self.paid.order_number])
        response = self.client.post(url, {"status": "shipped"}, follow=True)
        self.assertContains(response, "Order status changed to Shipped.")
        self.paid.refresh_from_db()
        self.assertEqual(self.paid.status, "shipped")

    def test_status_change_requires_post_and_valid_status(self):
        """US-15: GET is refused and unknown statuses are rejected."""
        url = reverse("dashboard:order_status",
                      args=[self.paid.order_number])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url, {"status": "lost"})
        self.paid.refresh_from_db()
        self.assertEqual(self.paid.status, "paid")


class MessagesSectionTests(DashboardTestCase):
    """US-27: Contact messages: list, filter, reply and mark handled."""

    def setUp(self):
        super().setUp()
        self.open = ContactMessage.objects.create(
            name="Niamh", email="niamh@example.com", subject="wholesale",
            message="Do you supply restaurants in Galway?",
        )
        ContactMessage.objects.create(
            name="Done", email="done@example.com", subject="other",
            message="Already answered this one.", handled=True,
        )
        self.client.force_login(self.admin)

    def test_filter_unhandled(self):
        """US-27: the list can show only messages not yet handled."""
        response = self.client.get(
            reverse("dashboard:messages"), {"handled": "no"}
        )
        self.assertEqual(list(response.context["page"]), [self.open])

    def test_detail_has_reply_link(self):
        """US-27: the message page has a mailto link to reply."""
        response = self.client.get(
            reverse("dashboard:message_detail", args=[self.open.pk])
        )
        self.assertContains(response, "Do you supply restaurants in Galway?")
        self.assertContains(
            response, 'href="mailto:niamh@example.com?subject=Re%3A%20'
        )

    def test_mark_as_handled(self):
        """US-27: "mark as handled" is a POST and updates the message."""
        url = reverse("dashboard:message_handled", args=[self.open.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url, {"handled": "1"})
        self.open.refresh_from_db()
        self.assertTrue(self.open.handled)
        self.client.post(url, {"handled": "0"})
        self.open.refresh_from_db()
        self.assertFalse(self.open.handled)


class ReviewsSectionTests(DashboardTestCase):
    """US-18 / US-19: Staff can list, filter and delete reviews."""

    def setUp(self):
        super().setUp()
        wine = self.wine("Reviewed Red")
        self.good = Review.objects.create(
            wine=wine, user=self.customer, rating=5, title="Great",
            body="Loved it", verified_purchase=True,
        )
        self.bad = Review.objects.create(
            wine=wine, user=self.admin, rating=1, title="Spam", body="Buy"
        )
        self.client.force_login(self.admin)

    def test_filter_by_rating(self):
        """US-19: reviews can be filtered by rating."""
        response = self.client.get(
            reverse("dashboard:reviews"), {"rating": "1"}
        )
        self.assertEqual(list(response.context["page"]), [self.bad])

    def test_delete_needs_confirmation_then_post(self):
        """US-19: GET asks for confirmation; POST deletes the review."""
        url = reverse("dashboard:review_delete", args=[self.bad.pk])
        response = self.client.get(url)
        self.assertContains(response, "Are you sure you want to delete")
        self.assertTrue(Review.objects.filter(pk=self.bad.pk).exists())
        response = self.client.post(url)
        self.assertRedirects(response, reverse("dashboard:reviews"))
        self.assertFalse(Review.objects.filter(pk=self.bad.pk).exists())
        self.assertTrue(Review.objects.filter(pk=self.good.pk).exists())


class RegionsSectionTests(DashboardTestCase):
    """US-09: Regions can be added and edited, with validation."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.add_url = reverse("dashboard:region_add")

    def test_add_region(self):
        """US-09: a new region is saved with a slug from name and country."""
        response = self.client.post(
            self.add_url, {"name": "Douro", "country": "Portugal"}
        )
        self.assertRedirects(response, reverse("dashboard:regions"))
        region = Region.objects.get(name="Douro")
        self.assertEqual(region.slug, "douro-portugal")

    def test_duplicate_region_is_rejected(self):
        """US-09: the same name and country can't be added twice."""
        response = self.client.post(
            self.add_url, {"name": "rioja", "country": "SPAIN"}
        )
        self.assertContains(
            response, "A region with this name and country already exists."
        )
        self.assertEqual(Region.objects.count(), 1)

    def test_required_fields(self):
        """US-09: name and country are both required."""
        response = self.client.post(self.add_url, {"name": "", "country": ""})
        self.assertContains(response, "Please enter the region&#x27;s name.")
        self.assertContains(response, "Please enter the country.")

    def test_edit_region(self):
        """US-09: a region can be renamed; clashing with another fails."""
        other = Region.objects.create(name="Douro", country="Portugal")
        url = reverse("dashboard:region_edit", args=[self.region.pk])
        self.client.post(url, {"name": "Rioja Alta", "country": "Spain"})
        self.region.refresh_from_db()
        self.assertEqual(self.region.name, "Rioja Alta")

        response = self.client.post(
            url, {"name": other.name, "country": other.country}
        )
        self.assertContains(response, "already exists")
        self.region.refresh_from_db()
        self.assertEqual(self.region.name, "Rioja Alta")


def make_store_manager(email="manager@example.com"):
    """A normal user (not staff, not superuser) in the Store Manager group."""
    user = User.objects.create_user(
        email=email, username=email.split("@")[0], password="x"
    )
    user.groups.add(Group.objects.get(name="Store Manager"))
    return user


class StoreManagerRoleTests(DashboardTestCase):
    """US-04 / US-09 / US-15: The Store Manager role."""

    def setUp(self):
        super().setUp()
        self.manager = make_store_manager()

    def test_group_exists_with_the_permission(self):
        """US-04: the Store Manager group exists after migrations."""
        group = Group.objects.get(name="Store Manager")
        codenames = list(group.permissions.values_list(
            "content_type__app_label", "codename"
        ))
        self.assertEqual(codenames, [("dashboard", "access_dashboard")])
        self.assertFalse(self.manager.is_staff)
        self.assertFalse(self.manager.is_superuser)
        self.assertTrue(self.manager.has_perm(DASHBOARD_PERMISSION))
        self.assertFalse(self.customer.has_perm(DASHBOARD_PERMISSION))

    def test_manager_can_open_every_dashboard_page(self):
        """US-15: a store manager can open every dashboard page."""
        self.client.force_login(self.manager)
        for method, url in self.dashboard_urls():
            if method == "get":
                with self.subTest(url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_manager_can_use_product_management(self):
        """US-09: a store manager can add, edit and delete wines."""
        wine = self.wine("Managed Red")
        self.client.force_login(self.manager)
        for url in [
            reverse("wine_add"),
            reverse("wine_edit", args=[wine.slug]),
            reverse("wine_delete", args=[wine.slug]),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(reverse("wine_delete", args=[wine.slug]))
        self.assertFalse(Wine.objects.filter(pk=wine.pk).exists())

    def test_manager_sees_product_links_and_hidden_wines(self):
        """US-09: edit links show, and unavailable wine pages still open."""
        wine = self.wine("Hidden Red", is_available=False)
        visible = self.wine("Shown Red")
        self.client.force_login(self.manager)
        response = self.client.get(reverse("wine_list"))
        self.assertContains(response, reverse("wine_edit",
                                              args=[visible.slug]))
        detail = self.client.get(reverse("wine_detail", args=[wine.slug]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "hidden from customers")

    def test_manager_cannot_open_django_admin(self):
        """US-04: a store manager has no Django admin access."""
        self.client.force_login(self.manager)
        for url in ["/admin/", reverse("admin:orders_order_changelist")]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith("/admin/login/"))

    def test_manager_dashboard_shows_email_and_logout(self):
        """US-15: the dashboard shows the manager's email and a logout."""
        self.client.force_login(self.manager)
        response = self.client.get(reverse("dashboard:overview"))
        self.assertContains(response, "manager@example.com")
        self.assertContains(
            response,
            f'<form method="POST" action="{reverse("account_logout")}">',
        )
        self.assertNotContains(response, "Django admin")

    def test_superuser_dashboard_has_django_admin_link(self):
        """US-04: only superusers see the Django admin link."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:overview"))
        self.assertContains(response, f'href="{reverse("admin:index")}"')
        self.assertContains(response, "Django admin")
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_customer_is_still_refused(self):
        """US-04: a customer can't use the dashboard or manage wines."""
        self.client.force_login(self.customer)
        for url in [reverse("dashboard:overview"), reverse("wine_add")]:
            with self.subTest(url=url):
                self.assertRedirects(
                    self.client.get(url), reverse("wine_list"),
                    fetch_redirect_response=False,
                )
