from django.db import models
from django.utils import timezone
from django.conf import settings
from main.models import Recipe, RecipeIngredient, Creatable
from common.utils import create_uuid_filename, filename_from_path
import wget
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

    def publish(self, commit=True):
        inst = self.publish_inst if self.publish_inst else self.PUBLISH_TO[0]()
        for field in self.PUB_FIELDS:
            setattr(inst, field, getattr(self, field))  # Copy publish fields
        self.published, self.seen, self.processed = (True, True, True)
        self.publish_date = timezone.now()
        if commit:
            inst.save()
            self.publish_inst = inst  # Must be after inst.save()
            self.save()
            self.publish_m2m()
        return inst

    def get_related_fields(self):
        klass = globals()[self.__class__.__name__]
        return [
            f for f in klass._meta.get_fields()
            if (f.one_to_many or f.one_to_one)
               and f.auto_created and not f.concrete
        ]

    def publish_m2m(self):
        fields = self.get_related_fields()
        print(fields)
        for f in fields:
            for inst in getattr(self, f.related_name).all():
                print(inst)
                inst.publish()

    def prepopulate_with_raw(self):
        """"
        Prepopulate pub fields as defined by AUTOPOP_FIELDS.

        AUTOPOP_FIELDS is a tuple containing field pairs.
        Field pairs contain a pub field at index 0 and raw field at index 1.
        In the 3rd position may be the name of a method of self, which takes
        the raw field as its argument and returns the result to the pub field.
        """
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
        return self.checksum != hashlib.md5(values.encode('utf-8')).hexdigest()

    @property
    def publish_inst(self):
        return getattr(self, self.PUBLISH_TO[1])

    @publish_inst.setter
    def publish_inst(self, inst=None):
        """Saves the supplied instance and sets it as the publish instance in one step."""
        if inst:
            inst.save()
            setattr(self, self.PUBLISH_TO[1], inst)
        else:
            self.publish_inst.save()

    def prepopulate_image(self, s3):
        fname = filename_from_path(self.image_url_raw)
        new_fname = create_uuid_filename(fname)
        fpath = wget.download(self.image_url_raw, '%s%s' % (settings.TMP_PATH, new_fname))
        s3.meta.client.upload_file(fpath, 'fdme-raw-img', new_fname)
        self.image_url = '{}{}'.format(settings.CDN_URL, new_fname)
        self.save()

    @property
    def publish_class(self):
        self.PUBLISH_TO[0]

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
    recipe_draft = models.ForeignKey(RecipeDraft, on_delete=models.CASCADE,
                                     related_name='ingredients')
    recipe_ingredient = models.ForeignKey(RecipeIngredient, on_delete=models.CASCADE,
                                          null=True, blank=True)

    def save(self, *args, **kwargs):
        self.generate_checksum()
        return super(IngredientDraft, self).save(*args, **kwargs)

    def __str__(self):
        return self.raw_text

    def publish(self):
        inst = super(IngredientDraft, self).publish(commit=False)
        inst.recipe = self.recipe_draft.recipe
        inst.match_ingredient_from(self.ingredient)
        self.publish_inst = inst
        self.save()
        self.publish_m2m()