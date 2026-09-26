import json
from django.test import TestCase, Client
from django.urls import reverse
from products.models import Wine, Region


class SommelierQuizTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.quiz_submit_url = reverse('quiz_submit')

        # Create test region
        self.region = Region.objects.create(name='Bordeaux', country='France')

        # Create test wines with different types and characteristics
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

    def test_quiz_page_loads(self):
        response = self.client.get(reverse('quiz_start'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sommelier/quiz.html')

    def test_quiz_submit_with_valid_answers(self):
        answers = {
            'type': 'red',
            'occasion': 'dinner',
            'food': 'meat',
            'style': 'bold',
            'budget': '20to35'
        }
        response = self.client.post(
            self.quiz_submit_url,
            data=json.dumps({'answers': answers}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('wines', data)
        self.assertIsInstance(data['wines'], list)
        # Red wine (25€) should be in results for red/meat/bold/20-35 budget
        wine_names = [w['name'] for w in data['wines']]
        self.assertIn('Red Wine Test', wine_names)

    def test_quiz_submit_handles_budget_filter(self):
        # With budget under €20, should exclude wines over €20
        answers = {
            'type': 'white',
            'occasion': 'casual',
            'food': 'none',
            'style': 'light',
            'budget': 'under20'
        }
        response = self.client.post(
            self.quiz_submit_url,
            data=json.dumps({'answers': answers}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        wines = data['wines']
        # Should only include wine_white (18€) and wine_cheap (12€)
        for wine in wines:
            price = float(wine['price'])
            self.assertLessEqual(price, 20)

    def test_quiz_submit_missing_answers(self):
        # Missing 'budget' answer
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
        response = self.client.post(
            self.quiz_submit_url,
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_quiz_submit_empty_answers(self):
        response = self.client.post(
            self.quiz_submit_url,
            data=json.dumps({'answers': {}}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)

    def test_quiz_submit_rejects_get_request(self):
        response = self.client.get(self.quiz_submit_url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_quiz_submit_never_returns_unavailable_wines(self):
        # Make all wines unavailable and answer comprehensively
        self.wine_red.is_available = False
        self.wine_red.save()
        self.wine_white.is_available = False
        self.wine_white.save()
        self.wine_expensive.is_available = False
        self.wine_expensive.save()
        self.wine_cheap.is_available = False
        self.wine_cheap.save()

        answers = {
            'type': 'red',
            'occasion': 'dinner',
            'food': 'meat',
            'style': 'bold',
            'budget': '35plus'
        }
        response = self.client.post(
            self.quiz_submit_url,
            data=json.dumps({'answers': answers}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['wines']), 0)

    def test_quiz_submit_returns_correct_wine_format(self):
        answers = {
            'type': 'red',
            'occasion': 'dinner',
            'food': 'meat',
            'style': 'bold',
            'budget': '20to35'
        }
        response = self.client.post(
            self.quiz_submit_url,
            data=json.dumps({'answers': answers}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if data['wines']:
            wine = data['wines'][0]
            self.assertIn('name', wine)
            self.assertIn('region', wine)
            self.assertIn('character', wine)
            self.assertIn('price', wine)
            self.assertIn('slug', wine)
            self.assertIn('image', wine)
            self.assertIn('type', wine)
            self.assertIn('cart_url', wine)

    def test_quiz_submit_respects_budget_constraints(self):
        # Budget 35+ should only include wine_expensive
        answers = {
            'type': 'red',
            'occasion': 'celebration',
            'food': 'meat',
            'style': 'bold',
            'budget': '35plus'
        }
        response = self.client.post(
            self.quiz_submit_url,
            data=json.dumps({'answers': answers}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for wine in data['wines']:
            price = float(wine['price'])
            self.assertGreater(price, 35)

    def test_quiz_submit_surprise_me_returns_random_wines(self):
        # Surprise me should return any available wine (within budget)
        answers = {
            'type': 'surprise',
            'occasion': 'casual',
            'food': 'none',
            'style': 'light',
            'budget': '35plus'
        }
        response = self.client.post(
            self.quiz_submit_url,
            data=json.dumps({'answers': answers}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('wines', data)
        # Should return wines over €35 (only wine_expensive qualifies)
        for wine in data['wines']:
            price = float(wine['price'])
            self.assertGreater(price, 35)
