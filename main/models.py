import random
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.utils.text import slugify
from django.utils.html import format_html_join
from timezone_field import TimeZoneField
from main.lib import weekdays
import logging
logger = logging.getLogger(__name__)


def get_name(self):
    if self.email:
        return self.email
    if self.first_name and self.last_name:
        return '{} {}'.format(self.first_name, self.last_name)
    else:
        return self.username


User.add_to_class("__str__", get_name)


def random_number():
    return random.randint(1, 1000000000)

def _get_cdn_image(url_str):
    return '%s%s' % (settings.CDN_URL, url_str.split('/')[-1:][0])


class LocationMissing(Exception):
    pass


class Creatable(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    created.short_description = 'Added'
    updated.short_description = 'Changed'

    class Meta:
        abstract = True

    def get_logs(self):
        """Get change logs for model."""
        from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
        from django.contrib.contenttypes.models import ContentType
        return LogEntry.objects.exclude(change_message="No fields changed.")\
                       .filter(content_type=ContentType.objects.get_for_model(self),
                               object_id=self.id).order_by('-action_time')[:20]


class Profile(models.Model):
    """
    https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fb_id = models.BigIntegerField(null=True, blank=True)
    photo_url = models.URLField(max_length=600, blank=True, default='')
    provider = models.CharField(max_length=55, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    country = models.CharField(max_length=255, blank=True, default='')
    state = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=255, blank=True, default='')
    firebase_id = models.CharField(max_length=400, default='', blank=True)
    age_min = models.PositiveSmallIntegerField(null=True, blank=True)
    age_max = models.PositiveSmallIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=55, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # These signals were meant to prevent multiple calls to save but they actually
    # broke the whole process.
    # @receiver(post_save, sender=User)
    # def create_user_profile(sender, instance, created, **kwargs):
    #     if created:
    #         Profile.objects.create(user=instance)
    #
    # @receiver(post_save, sender=User)
    # def save_user_profile(sender, instance, **kwargs):
    #     instance.profile.save()

    def __str__(self):
        return self.user.__str__()

    class Meta:
        unique_together = (('user', 'firebase_id'), )


class Blog(Creatable):
    author = models.CharField(max_length=255, blank=True, default='')
    image_url = models.URLField(blank=True, default='', max_length=600)
    title = models.CharField(max_length=255)
    url = models.URLField()
    firebase_id = models.CharField(max_length=255, default='', blank=True, unique=True)

    def __str__(self):
        return self.title


class Feedback(Creatable):
    """
    User feedback about the app itself
    """
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    has_positive_sentiment = models.BooleanField()
    gave_rating = models.BooleanField(default=False)
    content = models.TextField(blank=True, default='')


class Highlight(models.Model):
    """
    A restaurant might have a set of hightlights describing features or selling points.

    For example, "Vegetarian dishes" might be one and "Outdoor Seating" another.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True,
                            help_text="A slug helps query highlights via url")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Highlight, self).save(*args, **kwargs)


class Cuisine(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=50, unique=True,
                            help_text="A slug helps query cuisines via url")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Cuisine, self).save(*args, **kwargs)


class RecipeQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='recipe_queries')
    from_location = gis_models.PointField(default="POINT(0.0 0.0)")
    latitude = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    result_size = models.PositiveIntegerField(default=0)
    min_total_time = models.PositiveIntegerField(default=0, null=True)
    max_total_time = models.PositiveIntegerField(default=0, null=True)
    keywords = models.ManyToManyField('Keyword')
    tags = models.ManyToManyField('Tag')
    difficulty = models.CharField(max_length=25, default='')
    page = models.PositiveIntegerField(default=1)
    query_string = models.TextField(default='')
    created = models.DateTimeField(auto_now_add=True)

    def log(self, request, results):
        """
        Save a RecipeQuery from an API request.
        Logging a recipe query must never raise an exception.
        Caller expects RecipeQuery.log() to fail silently
        """
        try:
            qp = request.query_params
            self._set_params(qp, request, results)
            self.save()
            self._save_related(qp)
        except Exception as e:
            logger.error(str(e), exc_info=True, extra={
                'request': request
            })

    def _set_params(self, qp, request, results):
        self.query_string = request.META.get('QUERY_STRING', '')
        self.result_size = results
        self.user = request.user
        loc = qp.get('from_location', '').split(',')
        try:
            self.from_location = 'POINT({} {})'.format(*loc)
        except IndexError:
            pass
        self.min_total_time = qp.get('min_total_time')
        self.max_total_time = qp.get('max_total_time')
        self.difficulty = qp.getlist('difficulty')
        self.page = qp.get('page', 1)

    def _save_related(self, qp):
        self._save_m2m('Keyword', qp.getlist('keywords'))
        self._save_m2m('Tag', qp.getlist('tags'))

    def _save_m2m(self, mtm_class_name, mtm_list):
        mtm_class = globals()[mtm_class_name]
        if hasattr(mtm_class, 'slug') is False or mtm_list is None:
            return
        mtm_name = mtm_class_name.lower()+'s'
        for itm in mtm_list:
            if len(itm) < 1:
                continue
            try:
                obj = mtm_class.objects.get(slug=slugify(itm))
            except mtm_class.DoesNotExist:
                print('Cannot find', mtm_class_name, slugify(itm))
            else:
                getattr(self, mtm_name).add(obj)

    class Meta:
        verbose_name_plural = 'Recipe Queries'


class DishQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='dish_queries')
    from_location = gis_models.PointField(default="POINT(0.0 0.0)", db_index=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    max_distance_meters = models.PositiveIntegerField(null=True)
    result_size = models.PositiveIntegerField(default=0)
    min_price = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    max_price = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    keywords = models.ManyToManyField('Keyword')
    cuisines = models.ManyToManyField('Cuisine')
    highlights = models.ManyToManyField('Highlight')
    tags = models.ManyToManyField('Tag')
    has_delivery = models.BooleanField(default=False)
    has_booking = models.BooleanField(default=False)
    suburb = models.CharField(max_length=255, default='')
    page = models.PositiveIntegerField(default=1)
    query_string = models.TextField(default='')
    created = models.DateTimeField(auto_now_add=True)

    def log(self, request, results):
        """
        Save a DishQuery from an API request.
        Logging a dish query must never raise an exception.
        Caller expects DishQuery.log() to fail silently
        """
        try:
            qp = request.query_params
            self._set_params(qp, request, results)
            self.save()
            self._save_related(qp)
        except Exception as e:
            logger.error(str(e), exc_info=True, extra={
                'request': request
            })

    def _set_params(self, qp, request, results):
        self.query_string = request.META.get('QUERY_STRING', '')
        self.result_size = results
        self.user = request.user
        loc = qp.get('from_location', '').split(',')
        try:
            self.from_location = 'POINT({} {})'.format(*loc)
        except IndexError:
            pass
        try:
            self.max_distance_meters = float(qp.get('max_distance_meters'))
        except TypeError:
            pass
        self.min_price = qp.get('min_price')
        self.max_price = qp.get('max_price')
        self.has_delivery = bool(qp.get('has_delivery', False))
        self.has_booking = bool(qp.get('has_booking', False))
        self.page = qp.get('page', 1)
        try:
            self.suburb = ', '.join(qp.getlist('suburb'))
        except TypeError:
            pass

    def _save_related(self, qp):
        self._save_m2m('Keyword', qp.getlist('keywords'))
        self._save_m2m('Cuisine', qp.getlist('cuisines'))
        self._save_m2m('Highlight', qp.getlist('highlights'))
        self._save_m2m('Tag', qp.getlist('tags'))

    def _save_m2m(self, mtm_class_name, mtm_list):
        mtm_class = globals()[mtm_class_name]
        if hasattr(mtm_class, 'slug') is False or mtm_list is None:
            return
        mtm_name = mtm_class_name.lower()+'s'
        for itm in mtm_list:
            if len(itm) < 1:
                continue
            try:
                obj = mtm_class.objects.get(slug=slugify(itm))
            except mtm_class.DoesNotExist:
                print('Cannot find', mtm_class_name, slugify(itm))
            else:
                getattr(self, mtm_name).add(obj)

    def save(self, *args, **kwargs):
        self.latitude = self.from_location.y
        self.longitude = self.from_location.x
        return super(DishQuery, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Dish Queries'


class Restaurant(Creatable):
    name = models.CharField(max_length=255)
    slug = models.SlugField(default='', unique=True)
    image_url = models.URLField(max_length=600)
    address = models.TextField(blank=True, default='')
    cuisines = models.ManyToManyField(Cuisine)
    information = models.TextField(blank=True, default='')
    highlights = models.ManyToManyField(Highlight)
    blogs = models.ManyToManyField(Blog, related_name='restaurant')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    suburb = models.CharField(max_length=55, blank=True, default='')
    instagram_user = models.CharField(max_length=61, blank=True, default='')
    time_offset_minutes = models.IntegerField(help_text="Multiply hours by 60",
                                              default=0)
    timezone = TimeZoneField(default='', blank=True)
    tripadvisor_widget = models.TextField(blank=True, default='')
    location = gis_models.PointField(default="POINT(0.0 0.0)", blank=True, db_index=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, default=0)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, default=0)
    firebase_id = models.CharField(max_length=255, default='', blank=True, unique=True)
    quandoo_id = models.BigIntegerField(blank=True, null=True)
    delivery_provider = models.ForeignKey('DeliveryProvider', on_delete=models.SET_NULL,
                                          null=True, blank=True)
    delivery_link = models.URLField(max_length=512, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return '/restaurants/{0}/'.format(self.slug)

    def location_to_latlong(self):
        self.latitude = self.location.y
        self.longitude = self.location.x

    def time_offset_hours(self):
        return self.time_offset_minutes / 60

    def cuisine_list_html(self):
        return format_html_join(
            '\n', '{}<br>', ((cuisine.name, ) for cuisine in self.cuisines.all())
        )
    cuisine_list_html.short_description = 'cuisines'

    def cuisine_list(self):
        return ', '.join([c.name for c in self.cuisines.all()])

    def highlight_list_html(self):
        return format_html_join(
            '\n', '{}<br>', ((highlight.name, ) for highlight in self.highlights.all())
        )
    highlight_list_html.short_description = 'highlights'

    def get_displayable_opening_times(self):
        opening_times = []
        for weekday in list(weekdays.DAYWEEK_MAP.keys()):
            openingtimes_set = self.opening_times.filter(day_of_week=weekday)
            for opentime in openingtimes_set:
                opening_times.append(opentime.display_format())
            if len(openingtimes_set) == 0:
                opening_times.append((weekdays.convert(weekday), 'CLOSED', ''))
        return opening_times

    def app_opening_times(self):
        opening_times = {}
        for weekday in list(weekdays.DAYWEEK_MAP.keys()):
            weekday_long = weekdays.convert(weekday)
            day_arr = []
            openingtimes_set = self.opening_times.filter(day_of_week=weekday)
            for opentime in openingtimes_set:
                opens = opentime.as_seconds('opens') - (self.time_offset_minutes * 60)
                closes = opentime.as_seconds('closes') - (self.time_offset_minutes * 60)
                opentime_arr = [opens, closes]
                day_arr.append(opentime_arr)
            if len(day_arr) > 0:
                opening_times[weekday_long] = day_arr
        return opening_times

    def save(self, depth=0, *args, **kwargs):
        """
        Make slugs unique, geocode timezone.
        """
        self.location_to_latlong()
        if depth > 1000:
            print('Slug recursion error restaurant', self.name)
        if depth > 0:
            name = '{}-{}'.format(self.name, depth)
        else:
            name = self.name
        self.slug = slugify(name)
        try:
            Restaurant.objects.get(slug=self.slug)
        except Restaurant.DoesNotExist:
            return super(Restaurant, self).save(*args, **kwargs)
        except Restaurant.MultipleObjectsReturned:
            print("DANGER: Multiple restaurants for slug", self.slug)
        self.save(depth=depth+1, *args, **kwargs)


class DeliveryProvider(models.Model):
    """
    A provider of food delivery services
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=50, unique=True)
    title = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField()
    logo_url = models.URLField()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(DeliveryProvider, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class OpeningTime(models.Model):
    """
    Follows http://schema.org/OpeningHoursSpecification

    Ref http://stackoverflow.com/questions/1036603/storing-business-hours-in-a-database
    """
    SUNDAY = 'sun'
    MONDAY = 'mon'
    TUESDAY = 'tue'
    WEDNESDAY = 'wed'
    THURSDAY = 'thu'
    FRIDAY = 'fri'
    SATURDAY = 'sat'
    WEEKDAY_CHOICES = (
        (SUNDAY, 'Sunday'),
        (MONDAY, 'Monday'),
        (TUESDAY, 'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY, 'Thursday'),
        (FRIDAY, 'Friday'),
        (SATURDAY, 'Saturday')
    )
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,
                                   related_name='opening_times')
    opens = models.TimeField(help_text='24 hrs, e.g. 17:00 is 5pm')
    closes = models.TimeField(help_text='24 hrs, e.g. 17:00 is 5pm')
    day_of_week = models.CharField(max_length=3, choices=WEEKDAY_CHOICES)
    valid_from = models.DateField(null=True, blank=True)
    valid_through = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = (('restaurant', 'opens', 'closes', 'day_of_week',
                            'valid_from', 'valid_through'), )

    def __str__(self):
        return "{} Open: {}, Close: {}, {}".format(self.restaurant,
                                                   self.opens.isoformat(),
                                                   self.closes.isoformat(),
                                                   self.day_of_week)

    def display_format(self):
        return (self.get_day_of_week(),
                self.opens.strftime('%I:%M%p').lstrip('0'),
                self.closes.strftime('%I:%M%p').lstrip('0'))

    def get_day_of_week(self):
        return weekdays.convert(self.day_of_week)

    def as_seconds(self, field):
        if field not in ['opens', 'closes']:
            return None
        time = getattr(self, field)
        seconds = time.second
        seconds += time.minute * 60
        seconds += time.hour * 60 * 60
        return seconds


class Keyword(models.Model):
    """
    Keywords can be used to describe dishes.
    """
    CHEAPEATS_PRICE = 1500
    word = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True,
                            help_text="A slug helps query via url")

    def __str__(self):
        return self.word

    def save(self, *args, **kwargs):
        self.slug = slugify(self.word)
        super(Keyword, self).save(*args, **kwargs)

    @property
    def word_human(self):
        args = (r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', self.word)
        return re.sub(*args).title()


class Tag(models.Model):
    """
    Tags describe the attributes of dishes.
    Such as 'Bacon', 'Bacon and eggs', 'burger'.
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Tag, self).save(*args, **kwargs)


class DishesByUserQuerySet(models.QuerySet):
    M_IN_DEGREE = 111111

    def reduce_by_distance(self, location=None, meters=None):
        try:
            if len(location) * len(meters) > 0:
                point = Point(float(location[0]), float(location[1]))
                return self.filter(
                    restaurant__location__dwithin=(point, self._meters_to_degrees(meters))
                )
        except Exception as e:
            logger.error(str(e), exc_info=True)
        return self

    def distance(self, field, point):
        return self.annotate(distance=Distance(field, point))

    def order_by_distance(self, location):
        """Order dishes by their distance from user"""
        try:
            if len(location) == 2:
                point = Point(float(location[0]), float(location[1]), srid=4326)
                return self.distance('restaurant__location', point).order_by('distance')
        except Exception as e:
            logger.error(str(e), exc_info=True)
        return self

    def _meters_to_degrees(self, meters=0):
        return float(meters) / self.M_IN_DEGREE

    def not_liked(self, user):
        excl_qs = Dish.objects.filter(likes__user=user, likes__did_like=True)
        return self.exclude(id__in=excl_qs)

    def fresh(self, user):
        exclude_time = datetime.now(timezone.utc) - timedelta(hours=1)
        excl_qs = Dish.objects.filter(likes__user=user, likes__updated__gte=exclude_time)
        return self.exclude(id__in=excl_qs)

    def saved(self, user):
        return self.filter(likes__user=user, likes__did_like=True)


class Dish(Creatable):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,
                                   related_name='dishes')
    image_url = models.URLField(blank=True, default='', max_length=600)
    price = models.IntegerField(default=0)
    title = models.CharField(max_length=600)
    description = models.TextField(default='', blank=True)
    recipe = models.ForeignKey('Recipe', on_delete=models.SET_NULL, null=True,
                               related_name='dishes', blank=True)
    views_count = models.PositiveIntegerField(
        default=0,
        help_text='legacy calculated field from Firebase'
    )
    likes_count = models.PositiveIntegerField(
        default=0,
        help_text='legacy calculated field from Firebase'
    )
    instagram_user = models.CharField(max_length=61, blank=True, default='')
    keywords = models.ManyToManyField(Keyword)
    tags = models.ManyToManyField(Tag)
    firebase_id = models.CharField(max_length=255, default='', blank=True, unique=True)
    random = models.BigIntegerField(default=random_number)

    objects = DishesByUserQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return '/dish/{0}/'.format(self.id)

    def price_format(self):
        return "${0:.2f}".format(self.price/100)

    def keyword_list_html(self):
        return format_html_join(
            '\n', '{}<br>', ((keyword.word, ) for keyword in self.keywords.all())
        )
    keyword_list_html.short_description = 'keywords'

    def keyword_list(self):
        return ', '.join([k.word for k in self.keywords.all()])

    def tag_list_html(self):
        return format_html_join(
            '\n', '{}<br>', ((tag.name,) for tag in self.tags.all())
        )
    tag_list_html.short_description = 'tags'

    def tag_list(self):
        return ', '.join([t.name for t in self.tags.all()])

    def save_from_migration(self, *args, **kwargs):
        title = self.title
        description = ''
        arr_dash = title.split('-', maxsplit=2)
        arr_dot = title.split('. ', maxsplit=2)
        arr_com = title.split(',', maxsplit=2)
        if len(arr_dash) > 1:
            description = arr_dash[1].strip()
            title = arr_dash[0].strip()
        elif len(arr_dot) > 1:
            description = arr_dot[1].strip()
            title = arr_dot[0].strip()
        elif len(arr_com) > 1:
            description = arr_com[1].strip()
            title = arr_com[0].strip()
        self.title = title
        if len(description) > 0:
            self.description = description
        self.save(*args, **kwargs)

    def increment_views(self):
        self.views_count += 1
        self.save()

    def increment_likes(self):
        self.likes_count += 1
        self.save()

    def randomise(self):
        self.random = random.randint(1, 1000000000)
        self.save()

    def check_integrity(self):
        if self.price < Keyword.CHEAPEATS_PRICE:
            try:
                self.keywords.get(slug='cheapeats')
            except Keyword.DoesNotExist:
                self.keywords.add(Keyword.objects.get(slug='cheapeats'))
        else:
            try:
                kwd = self.keywords.get(slug='cheapeats')
                self.keywords.remove(kwd)
            except Keyword.DoesNotExist:
                pass

    class Meta:
        verbose_name_plural = 'Dishes'


class RecipesByUserQuerySet(models.QuerySet):
    def not_liked(self, user):
        try:
            excl_qs = self.filter(likes__user=user, likes__did_like=True)
            return self.exclude(id__in=excl_qs)
        except TypeError:
            """Exception raised for anonymous user."""
            return self

    def fresh(self, user):
        try:
            exclude_time = datetime.now(timezone.utc) - timedelta(hours=1)
            excl_qs = self.filter(likes__user=user, likes__updated__gte=exclude_time)
            return self.exclude(id__in=excl_qs)
        except TypeError:
            """Exception raised for anonymous user."""
            return self

    def saved(self, user):
        return self.filter(likes__user=user, likes__did_like=True)


class Recipe(Creatable):
    EASY = 'es'
    MODERATE = 'md'
    DIFFICULT = 'dt'
    DIFFICULTY_CHOICES = (
        (EASY, 'Easy'),
        (MODERATE, 'Moderate'),
        (DIFFICULT, 'Difficult'),
    )
    name = models.CharField(max_length=255, default='')
    description = models.TextField(default='', blank=True)
    image_url = models.URLField(blank=True, default='', max_length=600)
    prep_time_seconds = models.PositiveIntegerField(default=0)
    cook_time_seconds = models.PositiveIntegerField(default=0)
    total_time_seconds = models.PositiveIntegerField(default=0)
    servings = models.PositiveIntegerField(default=0)
    difficulty = models.CharField(default=EASY, choices=DIFFICULTY_CHOICES, max_length=3)
    notes = models.TextField(default='', blank=True)
    source_url = models.URLField(blank=True, default='', max_length=600, unique=True)
    keywords = models.ManyToManyField(Keyword, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    likes_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    random = models.BigIntegerField(default=random_number)

    objects = RecipesByUserQuerySet.as_manager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return '/recipe/{0}/{1}'.format(self.id, slugify(self.name))

    def save(self, *args, **kwargs):
        if self.prep_time_seconds is None:
            self.prep_time_seconds = 0
        self.total_time_seconds = self.prep_time_seconds + self.cook_time_seconds
        return super(Recipe, self).save(*args, **kwargs)

    def check_integrity(self):
        if settings.CDN_URL not in self.image_url and len(self.image_url) > 0:
            self.image_url = _get_cdn_image(self.image_url)
            self.save()

    def ingredient_text(self):
        txt = ''
        for ingr in self.ingredients.all():
                txt += '%s, ' % ingr.display
        return txt.rstrip(', ')
    ingredient_text.short_description = 'Ingredients'

    def get_source_url_display(self):
        url = urlparse(self.source_url)
        try:
            return url.hostname.replace("www.", "")
        except AttributeError:
            return ''

    def get_prep_time_display(self):
        return self._humanise_duration('prep_time_seconds')

    def get_cook_time_display(self):
        return self._humanise_duration('cook_time_seconds')

    def _humanise_duration(self, attrname):
        return '{} mins'.format(getattr(self, attrname) // 60)

    def keyword_list_html(self):
        return format_html_join(
            '\n', '{}<br>', ((keyword.word, ) for keyword in self.keywords.all())
        )
    keyword_list_html.short_description = 'keywords'

    def keyword_list(self):
        return ', '.join([k.word for k in self.keywords.all()])

    def tag_list_html(self):
        return format_html_join(
            '\n', '{}<br>', ((tag.name,) for tag in self.tags.all())
        )
    tag_list_html.short_description = 'tags'

    def tag_list(self):
        return ', '.join([t.name for t in self.tags.all()])

    def increment_views(self):
        self.views_count += 1
        self.save()

    def increment_likes(self):
        self.likes_count += 1
        self.save()

    def randomise(self):
        self.random = random.randint(1, 1000000000)
        self.save()

    def check_saved(self, user):
        try:
            like = self.likes.get(user=user)
            self.saved = like.did_like
        except AttributeError:
            self.saved = False
        except RecipeLike.DoesNotExist:
            self.saved = False
        except TypeError:
            self.saved = False
        return self.saved


class RecipeStep(Creatable):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name='steps')
    position = models.PositiveIntegerField(null=False, blank=False)
    text = models.TextField(default='')

    def __str__(self):
        return self.text


class Ingredient(Creatable):
    name = models.CharField(max_length=255, default='')
    description = models.TextField(default='', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (('name', 'description'), )


class RecipeIngredient(Creatable):
    MAIN = 'mn'
    SAUCE = 'sc'
    GARNISH = 'gn'
    SIDE = 'sd'
    TYPE_CHOICES = (
        (MAIN, 'Main'),
        (SAUCE, 'Sauce'),
        (GARNISH, 'Garnish'),
        (SIDE, 'Side')
    )
    FRACTION_CHOICES = (
        ('1/2', '1/2'), ('1/3', '1/3'), ('2/3', '2/3'), ('1/4', '1/4'), ('3/4', '3/4'),
        ('1/5', '1/5'), ('2/5', '2/5'), ('3/5', '3/5'), ('4/5', '4/5'), ('1/8', '1/8'),
        ('3/8', '3/8'), ('5/8', '5/8'), ('7/8', '7/8'), ('N/A', 'N/A')
    )
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE,
                               related_name='ingredients')
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE,
                                   related_name='recipes')
    quantity = models.DecimalField(max_digits=9, decimal_places=3, default=1.0)
    unit_type = models.CharField(max_length=127, default='', blank=True)
    ingredient_type = models.CharField(max_length=2, default=MAIN,
                                       blank=True, choices=TYPE_CHOICES)
    preparation = models.CharField(max_length=255, blank=True, default='')
    fraction = models.CharField(max_length=4, blank=True, default='N/A',
                                choices=FRACTION_CHOICES)
    uses_fractions = models.BooleanField(default=False, blank=True)

    @property
    def name(self):
        """Get ingredient name"""
        return self.ingredient.name

    @property
    def description(self):
        """Get ingredient description"""
        return self.ingredient.description

    @property
    def display(self):
        if self.uses_fractions and self.fraction:
            qty = self.fraction
        elif self.fraction != 'N/A':
            qty = '{:f}{}'.format(self.quantity.normalize(), self.fraction)
        else:
            qty = '{:f}'.format(self.quantity.normalize())
        ut = ' %s of' % self.unit_type if self.unit_type else ''
        prep = ', %s' % self.preparation if self.preparation else ''
        kwargs = {'quantity': qty, 'unit_type': ut, 'preparation': prep,
                  'ingredient': self.ingredient.name}
        return '{quantity}{unit_type} {ingredient}{preparation}'.format(**kwargs).lower()

    def match_ingredient_from(self, value):
        """Set the ingredient to one matching the supplied value."""
        try:
            ing = Ingredient.objects.filter(name__iexact=value)[0]
        except IndexError:
            ing = Ingredient.objects.create(name=value)
        finally:
            self.ingredient = ing

    def __str__(self):
        return self.display


class RecipeRequest(Creatable):
    dish = models.ForeignKey('Dish', on_delete=models.CASCADE,
                             related_name='recipe_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='recipe_request')

    def __str__(self):
        return self.dish.title


class View(Creatable):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='views')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='views')

    def save(self, *args, **kwargs):
        super(View, self).save(*args, **kwargs)
        self.dish.increment_views()


class Like(Creatable):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='likes')
    did_like = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super(Like, self).save(*args, **kwargs)
        if self.did_like:
            self.dish.increment_likes()
        LikeTransaction.objects.create(user=self.user, dish=self.dish,
                                       did_like=self.did_like)

    def __str__(self):
        return '{0} did{1} like {2}'.format(self.user, '' if self.did_like else ' not',
                                            self.dish)

    class Meta:
        unique_together = (('user', 'dish'), )


class LikeTransaction(Creatable):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='like_history')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='like_history')
    did_like = models.BooleanField(default=False)

    def __str__(self):
        return '{0} did{1} like {2}'.format(self.user, '' if self.did_like else ' not',
                                            self.dish)


class RecipeView(Creatable):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipe_views')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='views')

    def save(self, *args, **kwargs):
        super(RecipeView, self).save(*args, **kwargs)
        self.recipe.increment_views()


class RecipeLike(Creatable):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipe_likes')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='likes')
    did_like = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super(RecipeLike, self).save(*args, **kwargs)
        if self.did_like:
            self.recipe.increment_likes()
        RecipeLikeTransaction.objects.create(user=self.user, recipe=self.recipe,
                                             did_like=self.did_like)

    def __str__(self):
        return '{0} did{1} like {2}'.format(self.user, '' if self.did_like else ' not',
                                            self.recipe)

    class Meta:
        unique_together = (('user', 'recipe'), )


class RecipeLikeTransaction(Creatable):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='recipe_like_history')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='like_history')
    did_like = models.BooleanField(default=False)

    def __str__(self):
        return '{0} did{1} like {2}'.format(self.user, '' if self.did_like else ' not',
                                            self.recipe)


class RecipeRating(Creatable):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='recipe_ratings')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='ratings')
    rating = models.PositiveSmallIntegerField(default=0, null=True)

    class Meta:
        unique_together = (('user', 'recipe'), )


class RecipeCollection(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(default='', blank=True)
    image_url = models.URLField(blank=True, default='', max_length=600)
    recipes = models.ManyToManyField(Recipe, related_name='collections', blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return '/recipes/browse/%s/' % self.slug


class BookingProvider(models.Model):
    """
    A provider of restaurant booking services
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=50, unique=True)
    title = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    logo_url = models.URLField(blank=True, default='')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(BookingProvider, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class FulfilmentEvent(Creatable):
    delivery_provider = models.ForeignKey(
        DeliveryProvider, on_delete=models.CASCADE, related_name='fulfilments',
        null=True, blank=True)
    booking_provider = models.ForeignKey(
        BookingProvider, on_delete=models.CASCADE, related_name='fulfilments',
        null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fulfilments')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='fulfilments')


class Report(Creatable):
    """
    A report is a statement a user might make about the accuracy of restaurant data.
    """
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL,
                             related_name='reports')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,
                                   related_name='reports')
    content = models.TextField(default='')
    type = models.CharField(max_length=55)


def in_list(item, L):
    for i in L:
        if item in i:
            return L.index(i)
    return -1
