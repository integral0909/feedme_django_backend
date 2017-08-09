from django.core.management.base import BaseCommand
from django.db.models.functions import Lower
from main.models import *
from django_dedupe.deduplicator import Deduplicator


class RecipeDeduplicator(Deduplicator):
    queryset = Recipe.objects.all()
    fieldname = 'source_url'
    model = Recipe
    exclude_relations = ['ingredients', 'keywords', 'tags']


class IngredientDeduplicator(Deduplicator):
    queryset = Ingredient.objects.all()
    fieldname = 'name'
    field_func = Lower
    model = Ingredient


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('models', nargs='+', type=str)

    def handle(self, *args, **options):
        for model in options['models']:
            deduper = globals()[model.title() + 'Deduplicator']()
            deduper()

