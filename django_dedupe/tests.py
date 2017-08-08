from django.test import TestCase
from .deduplicator import Deduplicator
from main.models import Ingredient
from django.db.models.functions import Lower

class TestDeduplicator(TestCase):
    fixtures = ['fixtures/recipes_with_duplicates.json']
    def test_deduplicator(self):
        dd = Deduplicator(Ingredient.objects.all(),
                          'name', Lower, Ingredient)
        dd()


