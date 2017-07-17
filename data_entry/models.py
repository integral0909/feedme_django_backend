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
                 if (time_unit(v) == 'hours' or time_unit(v) == 'minutes')}
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
    published = models.BooleanField(default=False, help_text=SAVED_HELP)
    publish_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def publish(self):
        inst = self._get_pub_inst() if self._get_pub_inst() else self.PUBLISH_TO[0]()
        for field in self.PUB_FIELDS:
            setattr(inst, field, getattr(self, field))
        inst.save()
        setattr(self, self.PUBLISH_TO[1], inst)
        self.save()

    def prepopulate_with_raw(self):
        for field_pair in self.AUTOPOP_FIELDS:
            if len(field_pair) == 2:
                setattr(self, field_pair[0], getattr(self, field_pair[1]))
            elif len(field_pair) == 3:
                setattr(self, field_pair[0], getattr(self, field_pair[2])(field_pair[1]))

    def generate_checksum(self):
        values = ''.join([str(getattr(self, v)) for v in self.RAW_FIELDS])
        self.checksum = hashlib.md5(values.encode('utf-8')).hexdigest()

    def checksum_has_changed(self):
        values = ''.join([str(getattr(self, v)) for v in self.RAW_FIELDS])
        return self.checksum == hashlib.md5(values.encode('utf-8')).hexdigest()

    def _get_pub_inst(self):
        return getattr(self, self.PUBLISH_TO[1])

    def __str__(self):
        return getattr(self, self.RAW_FIELDS[0])



class RecipeDraft(Draft):
    RAW_FIELDS = ('name_raw', 'description_raw', 'prep_time_raw', 'source_url',
                  'servings_raw','cook_time_raw', 'difficulty_raw', 'image_url_raw')
    PUB_FIELDS = ('name', 'description', 'image_url', 'prep_time_seconds',
                  'cook_time_seconds', 'servings', 'difficulty', 'source_url')
    AUTOPOP_FIELDS = (('name', 'name_raw'), ('description', 'description_raw'),
                      ('servings', 'servings_raw'),
                      ('prep_time_seconds', 'prep_time_raw', '_parse_time_str'),
                      ('cook_time_seconds', 'cook_time_raw', '_parse_time_str'))
    PUBLISH_TO = (Recipe, 'recipe')
    name = models.CharField(max_length=255)
    name_raw = models.CharField(max_length=255)
    description = models.TextField(default='', blank=True)
    description_raw = models.TextField(default='', blank=True)
    image_url = models.URLField(blank=True, default='', max_length=600)
    image_url_raw = models.URLField(blank=True, default='', max_length=600)
    prep_time_raw = models.CharField(max_length=255, blank=True)
    prep_time_seconds = models.PositiveIntegerField(default=0)
    cook_time_raw = models.CharField(max_length=255, blank=True)
    cook_time_seconds = models.PositiveIntegerField(default=0)
    servings = models.PositiveIntegerField(default=0)
    servings_raw = models.CharField(max_length=55, default='', blank=True)
    difficulty_raw = models.CharField(max_length=255, blank=True)
    difficulty = models.CharField(default=Recipe.EASY, choices=Recipe.DIFFICULTY_CHOICES,
                                  max_length=3)
    source_url = models.URLField(blank=True, default='', max_length=600, unique=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=True, blank=True)

    def _parse_time_str(self, field):
        return parse_time_str(getattr(self, field))

    def save(self, *args, **kwargs):
        self.generate_checksum()
        return super(RecipeDraft, self).save(*args, **kwargs)


class IngredientDraft(Draft):
    RAW_FIELDS = ('raw_text', )
    PUB_FIELDS = ('quantity', 'unit_type', 'ingredient_type',
                  'preparation', 'fraction', 'uses_fractions')
    PUBLISH_TO = (RecipeIngredient, 'recipe_ingredient')
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

    def __str__(self):
        return self.raw_text

    def publish(self):
        super(IngredientDraft, self).publish()
        self.recipe_ingredient.match_ingredient_from(self.ingredient)
        # Needs to resolve ingredient against ingredient objects
        # Needs to