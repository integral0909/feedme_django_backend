from django.test import TestCase, Client
import logging

logging.disable(logging.CRITICAL)


class TestReactViews(TestCase):
    fixtures = [
        'fixtures/keywords.json',
        'fixtures/recipes_from_dev.json',
        'fixtures/recipe_collections.json'
    ]

    def setUp(self):
        self.c = Client()

    def test_homepage(self):
        res = self.c.get('/')
        self.assertEqual(res.status_code, 200)

    def test_recipepage(self):
        res = self.c.get('/recipe/97/lamb-kofka-meatballs-in-curry-sauce')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Lamb Kofka Meatballs In Curry Sauce')

    def test_recipepage_slugless(self):
        res = self.c.get('/recipe/97')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Lamb Kofka Meatballs In Curry Sauce')

    def test_recipe_collection(self):
        res = self.c.get('/recipe/browse/healthy-mini-snacks')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Healthy mini snacks')
