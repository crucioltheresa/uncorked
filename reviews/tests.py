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
            total_price=25.00,
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

    def test_delete_requires_login(self):
        """US-19: anonymous users cannot delete a review."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())
