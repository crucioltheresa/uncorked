import json
from django.test import TestCase, Client
from django.urls import reverse
from products.models import Wine, Region


class WineQuizTests(TestCase):
    """US-20: Wine quiz page and answer validation."""

    def setUp(self):
        self.client = Client()
        self.quiz_submit_url = reverse('quiz_submit')

    def test_quiz_page_loads(self):
        """US-20: quiz page loads with the quiz template."""
        response = self.client.get(reverse('quiz_start'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sommelier/quiz.html')

    def test_quiz_submit_missing_answers(self):
        """US-20: a missing answer returns a 400 error naming it."""
        answers = {
            'type': 'red',
            'occasion': 'dinner',
            'food': 'meat',
            'style': 'bold'
        }
        response = self.client.post(
            self.quiz_submit_url,
            data=json.dumps({'answers': answers}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('budget', data['error'])

    def test_quiz_submit_invalid_json(self):
        """US-20: invalid JSON returns a 400 error."""
        response = self.client.post(
            self.quiz_submit_url,
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_quiz_submit_empty_answers(self):
        """US-20: empty answers return a 400 error."""
        response = self.client.post(
            self.quiz_submit_url,
            data=json.dumps({'answers': {}}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_quiz_submit_rejects_get_request(self):
        """US-20: GET on the submit endpoint is not allowed."""
        response = self.client.get(self.quiz_submit_url)
        self.assertEqual(response.status_code, 405)


class QuizRecommendationTests(TestCase):
    """US-21: Wine recommendations from quiz answers."""

    def setUp(self):
        self.client = Client()
        self.quiz_submit_url = reverse('quiz_submit')
        self.region = Region.objects.create(name='Bordeaux', country='France')

        self.wine_red = Wine.objects.create(
            name='Red Wine Test',
            producer='Test Producer',
            wine_type='red',
            region=self.region,
            character='bold, rich, full-bodied',
            price='25.00',
            abv='13.5',
            food_pairing='red meat, cheese',
            is_available=True
        )
        self.wine_white = Wine.objects.create(
            name='White Wine Test',
            producer='Test Producer',
            wine_type='white',
            region=self.region,
            character='light, crisp, delicate',
            price='18.00',
            abv='12.0',
            food_pairing='seafood, cheese',
            is_available=True
        )
        self.wine_expensive = Wine.objects.create(
            name='Premium Wine Test',
            producer='Test Producer',
            wine_type='red',
            region=self.region,
            character='bold, robust, structured',
            price='50.00',
            abv='14.5',
            food_pairing='red meat',
            is_available=True
        )
        self.wine_cheap = Wine.objects.create(
            name='Budget Wine Test',
            producer='Test Producer',
            wine_type='white',
            region=self.region,
            character='light, fresh',
            price='12.00',
            abv='11.0',
            food_pairing='seafood',
            is_available=True
        )

    def submit(self, answers):
        return self.client.post(
            self.quiz_submit_url,
            data=json.dumps({'answers': answers}),
            content_type='application/json'
        )

    def test_quiz_submit_with_valid_answers(self):
        """US-21: valid answers return matching wine recommendations."""
        response = self.submit({
            'type': 'red',
            'occasion': 'dinner',
            'food': 'meat',
            'style': 'bold',
            'budget': '20to35'
        })
        self.assertEqual(response.status_code, 200)
        wine_names = [w['name'] for w in response.json()['wines']]
        self.assertIn('Red Wine Test', wine_names)

    def test_quiz_submit_handles_budget_filter(self):
        """US-21: under-20 budget returns only wines up to 20."""
        response = self.submit({
            'type': 'white',
            'occasion': 'casual',
            'food': 'none',
            'style': 'light',
            'budget': 'under20'
        })
        self.assertEqual(response.status_code, 200)
        for wine in response.json()['wines']:
            self.assertLessEqual(float(wine['price']), 20)

    def test_quiz_submit_never_returns_unavailable_wines(self):
        """US-21: unavailable wines are never recommended."""
        Wine.objects.update(is_available=False)
        response = self.submit({
            'type': 'red',
            'occasion': 'dinner',
            'food': 'meat',
            'style': 'bold',
            'budget': '35plus'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['wines']), 0)

    def test_quiz_submit_returns_correct_wine_format(self):
        """US-21: each recommendation includes all fields the page needs."""
        response = self.submit({
            'type': 'red',
            'occasion': 'dinner',
            'food': 'meat',
            'style': 'bold',
            'budget': '20to35'
        })
        self.assertEqual(response.status_code, 200)
        wine = response.json()['wines'][0]
        for field in ['name', 'region', 'character', 'price', 'slug',
                      'image', 'type', 'cart_url']:
            self.assertIn(field, wine)

    def test_quiz_submit_respects_budget_constraints(self):
        """US-21: 35-plus budget returns only wines over 35."""
        response = self.submit({
            'type': 'red',
            'occasion': 'celebration',
            'food': 'meat',
            'style': 'bold',
            'budget': '35plus'
        })
        self.assertEqual(response.status_code, 200)
        for wine in response.json()['wines']:
            self.assertGreater(float(wine['price']), 35)

    def test_quiz_submit_surprise_me_returns_random_wines(self):
        """US-21: surprise me returns available wines within budget."""
        response = self.submit({
            'type': 'surprise',
            'occasion': 'casual',
            'food': 'none',
            'style': 'light',
            'budget': '35plus'
        })
        self.assertEqual(response.status_code, 200)
        for wine in response.json()['wines']:
            self.assertGreater(float(wine['price']), 35)
