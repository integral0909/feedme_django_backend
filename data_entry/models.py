from django.db import models
from main.models import Recipe, RecipeIngredient, Creatable
import re
import hashlib


SEEN_HELP = "Has this item been seen by a human?"
PROCESSED_HELP = "Has this item had its values validated and adjusted by a human?"
SAVED_HELP = "Has this item been published in the live feed?"
HOUR_STRINGS = {'hrs', 'hr'}
MINUTE_STRINGS = {'mins', 'min'}


ALPHANUM_ONLY = re.compile('([^\s\w]|_)+')
REDUCED_VOWELS = re.compile('[aeoutAEOUT]')


def parse_time_str(val):
    try:
        words = ALPHANUM_ONLY.sub('', val).split()
    except AttributeError:
        pass
    else:
        times = {time_unit(v): int(words[k - 1]) for k, v in enumerate(words)
                 if (time_unit(v) == 'hours' or
                     time_unit(v) == 'minutes')}
        return times.get('minutes', 0) * 60 + (times.get('hours', 0) * 60 * 60)


def time_unit(val):
    val = REDUCED_VOWELS.sub('', val)
    if val in HOUR_STRINGS:
        return 'hours'
    if val in MINUTE_STRINGS:
        return 'minutes'


class Draft(Creatable):
    checksum = models.CharField(max_length=32, db_index=True, unique=True)
    seen = models.BooleanField(default=False, help_text=SEEN_HELP)
    processed = models.BooleanField(default=False, help_text=PROCESSED_HELP)
    saved = models.BooleanField(default=False, help_text=SAVED_HELP)
    publish_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def generate_checksum(self):
        values = ''.join([str(getattr(self, v)) for v in self.RAW_FIELDS])
        self.checksum = hashlib.md5(values.encode('utf-8')).hexdigest()



class RecipeDraft(Draft):
    RAW_FIELDS = ('name', 'description', 'image_url', 'prep_time_raw', 'cook_time_raw',
                  'servings', 'difficulty_raw', 'source_url')
    name = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    image_url = models.URLField(blank=True, default='', max_length=600)
    prep_time_raw = models.CharField(max_length=255, blank=True)
    prep_time_seconds = models.PositiveIntegerField(default=0)
    cook_time_raw = models.CharField(max_length=255, blank=True)
    cook_time_seconds = models.PositiveIntegerField(default=0)
    servings = models.PositiveIntegerField(default=0)
    difficulty_raw = models.CharField(max_length=255, blank=True)
    difficulty = models.CharField(default=Recipe.EASY, choices=Recipe.DIFFICULTY_CHOICES,
                                  max_length=3)
    source_url = models.URLField(blank=True, default='', max_length=600)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=True, blank=True)

    def _parse_time_str(self, field):
        return parse_time_str(getattr(self, field))

    def save(self, *args, **kwargs):
        self.generate_checksum()
        return super(RecipeDraft, self).save(*args, **kwargs)

    def publish(self):
        print("Ahhh i'm being published!")


class IngredientDraft(Draft):
    RAW_FIELDS = ('raw_text', )
    raw_text = models.TextField(default='')
    ingredient = models.CharField(max_length=255, default='')
    description = models.TextField(default='', blank=True)
    quantity = models.DecimalField(max_digits=9, decimal_places=3, default=1.0)
    unit_type = models.CharField(max_length=127, default='', blank=True)
    ingredient_type = models.CharField(max_length=2, default=RecipeIngredient.MAIN,
                                       blank=True, choices=RecipeIngredient.TYPE_CHOICES)
    preparation = models.CharField(max_length=255, blank=True, default='')
    fraction = models.CharField(max_length=4, blank=True, default='N/A',
                                choices=RecipeIngredient.FRACTION_CHOICES)
    uses_fractions = models.BooleanField(default=False, blank=True)
    recipe_draft = models.ForeignKey(RecipeDraft, on_delete=models.CASCADE)
    recipe_ingredient = models.ForeignKey(RecipeIngredient, on_delete=models.CASCADE,
                                          null=True, blank=True)

    def save(self, *args, **kwargs):
        self.generate_checksum()
        return super(IngredientDraft, self).save(*args, **kwargs)