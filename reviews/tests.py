from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from products.models import Wine, Region
from .models import Review

User = get_user_model()


class WriteReviewTests(TestCase):
    """US-18: Write a review."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Test Red",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.5,
            price=25.00,
            stock=10,
        )
        self.url = reverse("add_review", args=[self.wine.id])
        self.review_data = {
            "rating": 5,
            "title": "Lovely",
            "body": "Smooth and fruity.",
        }

    def test_review_requires_login(self):
        """US-18: anonymous users are redirected to login."""
        response = self.client.post(self.url, self.review_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login"))
        self.assertFalse(Review.objects.exists())

    def test_submit_review_creates_review(self):
        """US-18: a valid review is saved and the user returns to the wine."""
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.post(self.url, self.review_data)
        self.assertRedirects(
            response, reverse("wine_detail", args=[self.wine.slug])
        )
        self.assertTrue(
            Review.objects.filter(user=self.user, wine=self.wine).exists()
        )

    def test_duplicate_review_shows_warning(self):
        """US-18: a second review of the same wine shows a warning."""
        Review.objects.create(
            wine=self.wine, user=self.user, rating=4,
            title="First", body="First review.",
        )
        self.client.login(username="test@example.com", password="testpass123")
        response = self.client.post(self.url, self.review_data, follow=True)
        self.assertEqual(Review.objects.filter(user=self.user).count(), 1)
        self.assertContains(response, "You have already reviewed this wine.")

    def test_review_marked_verified_after_paid_order(self):
        """US-18: review is a verified purchase if the user paid for it."""
        order = Order.objects.create(
            user=self.user,
            full_name="Test User",
            email="test@example.com",
            address_line1="123 Main",
            city="City",
            postcode="12345",
            country="Spain",
            grand_total=25.00,
            status="paid",
        )
        OrderItem.objects.create(
            order=order, wine=self.wine, quantity=1, price_at_purchase=25.00
        )
        self.client.login(username="test@example.com", password="testpass123")
        self.client.post(self.url, self.review_data)
        review = Review.objects.get(user=self.user, wine=self.wine)
        self.assertTrue(review.verified_purchase)

    def test_review_not_verified_without_purchase(self):
        """US-18: review is not verified if the user never bought the wine."""
        self.client.login(username="test@example.com", password="testpass123")
        self.client.post(self.url, self.review_data)
        review = Review.objects.get(user=self.user, wine=self.wine)
        self.assertFalse(review.verified_purchase)


class DeleteReviewTests(TestCase):
    """US-19: Delete own review."""

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            username="owner",
            password="testpass123",
        )
        User.objects.create_user(
            email="other@example.com",
            username="other",
            password="testpass123",
        )
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Test Red",
            producer="Test Producer",
            region=region,
            wine_type="red",
            abv=13.5,
            price=25.00,
            stock=10,
        )
        self.review = Review.objects.create(
            wine=self.wine, user=self.owner, rating=4,
            title="Nice", body="Good value.",
        )
        self.url = reverse("delete_review", args=[self.review.id])

    def test_owner_can_delete_review(self):
        """US-19: the review owner can delete their review."""
        self.client.login(username="owner@example.com", password="testpass123")
        response = self.client.post(self.url)
        self.assertRedirects(
            response, reverse("wine_detail", args=[self.wine.slug])
        )
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_other_user_cannot_delete_review(self):
        """US-19: another user gets 404 and the review stays."""
        self.client.login(username="other@example.com", password="testpass123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())

    def test_delete_with_get_returns_405(self):
        """US-19: deleting a review with GET is not allowed."""
        self.client.login(username="owner@example.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())

    def test_delete_requires_login(self):
        """US-19: anonymous users cannot delete a review."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())


AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class ReviewFromOrderTests(TestCase):
    """US-18: Writing and editing reviews from the order page."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="buyer@example.com", username="buyer", password="x"
        )
        self.other = User.objects.create_user(
            email="other@example.com", username="other", password="x"
        )
        region = Region.objects.create(name="Rioja", country="Spain")
        self.wine = Wine.objects.create(
            name="Bought Red", producer="Test", region=region,
            wine_type="red", abv=13.5, price="20.00", stock=10,
        )
        self.not_bought = Wine.objects.create(
            name="Other Red", producer="Test", region=region,
            wine_type="red", abv=13.5, price="20.00", stock=10,
        )
        self.order = self.make_order(self.user, "shipped")
        self.url = reverse(
            "order_review", args=[self.order.order_number, self.wine.id]
        )
        self.order_path = reverse(
            "order_detail", args=[self.order.order_number]
        )
        self.data = {
            "rating": "5",
            "title": "Lovely",
            "body": "Bright cherry, would buy again.",
            "next": self.order_path,
        }
        self.client.force_login(self.user)

    def make_order(self, user, status):
        order = Order.objects.create(
            user=user, full_name="B", email=user.email,
            address_line1="1 Main St", city="Dublin", postcode="D02 X285",
            country="Ireland", grand_total="20.00", status=status,
        )
        OrderItem.objects.create(
            order=order, wine=self.wine, quantity=1,
            price_at_purchase="20.00",
        )
        return order

    def test_submit_creates_verified_review_and_returns_to_order(self):
        """US-18: a review from the order page is verified; back to order."""
        response = self.client.post(self.url, self.data)
        self.assertRedirects(response, self.order_path)
        review = Review.objects.get(user=self.user, wine=self.wine)
        self.assertTrue(review.verified_purchase)
        self.assertEqual(review.rating, 5)

    def test_fetch_success_returns_json(self):
        """US-18: fetch requests get JSON with the saved review."""
        response = self.client.post(self.url, self.data, **AJAX)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        review = Review.objects.get(user=self.user, wine=self.wine)
        self.assertTrue(data["ok"])
        self.assertEqual(data["review"]["id"], review.id)
        self.assertEqual(data["review"]["wine_id"], self.wine.id)
        self.assertTrue(data["review"]["verified_purchase"])
        self.assertEqual(
            data["review"]["edit_url"],
            reverse("edit_review", args=[review.id]),
        )

    def test_fetch_errors_return_json(self):
        """US-18: invalid reviews return 400 JSON with the field errors."""
        response = self.client.post(
            self.url, {"rating": "9", "title": "", "body": ""}, **AJAX
        )
        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertIn("rating", errors)
        self.assertIn("title", errors)
        self.assertIn("body", errors)
        self.assertFalse(Review.objects.exists())

    def test_only_one_review_per_wine(self):
        """US-18: a second review of the same wine is refused."""
        self.client.post(self.url, self.data)
        response = self.client.post(self.url, self.data, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "already reviewed", response.json()["form_errors"][0]
        )
        self.assertEqual(Review.objects.count(), 1)

    def test_cannot_review_a_wine_not_bought(self):
        """US-18: the orders flow refuses a wine that isn't in the order."""
        url = reverse(
            "order_review",
            args=[self.order.order_number, self.not_bought.id],
        )
        self.assertEqual(self.client.post(url, self.data).status_code, 404)
        self.assertFalse(Review.objects.exists())

    def test_cannot_review_from_unpaid_or_someone_elses_order(self):
        """US-18: pending orders and other people's orders are refused."""
        pending = self.make_order(self.user, "pending")
        theirs = self.make_order(self.other, "paid")
        for order in [pending, theirs]:
            url = reverse(
                "order_review", args=[order.order_number, self.wine.id]
            )
            with self.subTest(status=order.status, owner=order.user.email):
                response = self.client.post(url, self.data)
                self.assertEqual(response.status_code, 404)
        self.assertFalse(Review.objects.exists())

    def test_unavailable_wine_can_still_be_reviewed(self):
        """US-18: a wine that's no longer sold can still be reviewed."""
        Wine.objects.filter(pk=self.wine.pk).update(is_available=False)
        response = self.client.post(self.url, self.data, **AJAX)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Review.objects.filter(wine=self.wine).exists())

    def test_edit_updates_the_review(self):
        """US-18: the owner can edit their review (JSON and redirect)."""
        review = Review.objects.create(
            wine=self.wine, user=self.user, rating=2, title="Meh", body="Ok"
        )
        url = reverse("edit_review", args=[review.id])
        data = dict(self.data, rating="4", title="Grew on me")
        response = self.client.post(url, data, **AJAX)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["review"]["rating"], 4)
        review.refresh_from_db()
        self.assertEqual(review.title, "Grew on me")
        # Bought since: the edit makes it a verified purchase
        self.assertTrue(review.verified_purchase)

        response = self.client.post(url, dict(data, title="Final"))
        self.assertRedirects(response, self.order_path)
        review.refresh_from_db()
        self.assertEqual(review.title, "Final")

    def test_edit_errors_return_json(self):
        """US-18: invalid edits return 400 JSON and change nothing."""
        review = Review.objects.create(
            wine=self.wine, user=self.user, rating=3, title="Fine", body="Ok"
        )
        url = reverse("edit_review", args=[review.id])
        response = self.client.post(url, {"rating": "3", "title": ""}, **AJAX)
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.json()["errors"])
        review.refresh_from_db()
        self.assertEqual(review.title, "Fine")

    def test_other_user_cannot_edit(self):
        """US-18: only the review's owner can edit it."""
        review = Review.objects.create(
            wine=self.wine, user=self.user, rating=3, title="Mine", body="Ok"
        )
        url = reverse("edit_review", args=[review.id])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.post(url, dict(self.data, title="Hacked"))
        self.assertEqual(response.status_code, 404)
        review.refresh_from_db()
        self.assertEqual(review.title, "Mine")

    def test_edit_page_is_prefilled_for_no_javascript(self):
        """US-18: the edit page shows the review for the owner."""
        review = Review.objects.create(
            wine=self.wine, user=self.user, rating=3, title="Pre-filled",
            body="Ok",
        )
        response = self.client.get(
            reverse("edit_review", args=[review.id]),
            {"next": self.order_path},
        )
        self.assertContains(response, 'value="Pre-filled"')
        self.assertContains(
            response, f'name="next" value="{self.order_path}"'
        )

    def test_wine_page_review_counts_shipped_orders_as_verified(self):
        """US-18: the wine page form also verifies shipped purchases."""
        url = reverse("add_review", args=[self.wine.id])
        response = self.client.post(url, self.data)
        self.assertRedirects(response, self.order_path)
        self.assertTrue(
            Review.objects.get(user=self.user).verified_purchase
        )
