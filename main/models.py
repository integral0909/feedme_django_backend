from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.gis.db import models as gis_models
from django.utils.text import slugify
from django.utils.html import format_html, format_html_join
from main.lib import weekdays


class Creatable(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    created.short_description = 'Added'
    updated.short_description = 'Changed'

    class Meta:
        abstract = True


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


class Restaurant(Creatable):
    name = models.CharField(max_length=255)
    slug = models.SlugField(default='')
    image_url = models.URLField(max_length=600)
    address = models.TextField(blank=True, default='')
    cuisines = models.ManyToManyField(Cuisine)
    information = models.TextField(blank=True, default='')
    highlights = models.ManyToManyField(Highlight)
    blogs = models.ManyToManyField(Blog)
    phone_number = models.CharField(max_length=20, blank=True, default='')
    suburb = models.CharField(max_length=55, blank=True, default='')
    instagram_user = models.CharField(max_length=61, blank=True, default='')
    time_offset_minutes = models.IntegerField(help_text="Multiply hours by 60",
                                              default=0)
    tripadvisor_widget = models.TextField(blank=True, default='')
    location = gis_models.PointField(default="POINT(0.0 0.0)", blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    firebase_id = models.CharField(max_length=255, default='', blank=True, unique=True)
    quandoo_id = models.BigIntegerField(blank=True, null=True)
    delivery_provider = models.ForeignKey('DeliveryProvider', on_delete=models.SET_NULL,
                                          null=True, blank=True)
    delivery_link = models.URLField(max_length=512, blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.latitude = self.location.y
        self.longitude = self.location.x
        super(Restaurant, self).save(*args, **kwargs)

    def time_offset_hours(self):
        return self.time_offset_minutes / 60

    def cuisine_list_html(self):
        return format_html_join(
            '\n', '{}<br>', ((cuisine.name, ) for cuisine in self.cuisines.all())
        )
    cuisine_list_html.short_description = 'cuisines'

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
        Make slugs unique
        """
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
    opens = models.TimeField()
    closes = models.TimeField()
    day_of_week = models.CharField(max_length=3, choices=WEEKDAY_CHOICES)
    valid_from = models.DateField(null=True, blank=True)
    valid_through = models.DateField(null=True, blank=True)

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
    word = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True,
                            help_text="A slug helps query via url")

    def __str__(self):
        return self.word

    def save(self, *args, **kwargs):
        self.slug = slugify(self.word)
        super(Keyword, self).save(*args, **kwargs)


class Dish(Creatable):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,
                                   related_name='dishes')
    image_url = models.URLField(blank=True, default='', max_length=600)
    price = models.IntegerField(default=0)
    title = models.CharField(max_length=255)
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
    firebase_id = models.CharField(max_length=255, default='', blank=True, unique=True)

    def __str__(self):
        return self.title

    def price_format(self):
        return "${0:.2f}".format(self.price/100)

    def keyword_list_html(self):
        return format_html_join(
            '\n', '{}<br>', ((keyword.word, ) for keyword in self.keywords.all())
        )
    keyword_list_html.short_description = 'keywords'


class Like(Creatable):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='likes')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE,
                             related_name='likes')
    did_like = models.BooleanField(default=False)


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
