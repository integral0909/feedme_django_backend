from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.gis.db import models as gis_models


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
    photo_url = models.URLField(max_length=255, blank=True, default='')
    provider = models.CharField(max_length=55, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    country = models.CharField(max_length=255, blank=True, default='')
    state = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=255, blank=True, default='')
    firebase_id = models.CharField(max_length=255, default='', blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()


class Blog(Creatable):
    author = models.CharField(max_length=255, blank=True, default='')
    image_url = models.URLField(blank=True, default='')
    title = models.CharField(max_length=255)
    url = models.URLField()
    firebase_id = models.CharField(max_length=255, default='', blank=True, unique=True)


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
    slug = models.SlugField(max_length=100,
                            help_text="A slug helps query highlights via url")

    def __str__(self):
        return self.name


class Cuisine(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=50,
                            help_text="A slug helps query cuisines via url")

    def __str__(self):
        return self.name


class Restaurant(Creatable):
    name = models.CharField(max_length=255)
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

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.latitude = self.location.y
        self.longitude = self.location.x
        super(Restaurant, self).save(*args, **kwargs)


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


class Keyword(models.Model):
    """
    Keywords can be used to describe dishes.
    """
    word = models.CharField(max_length=255, unique=True)


class Dish(Creatable):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,
                                   related_name='dishes')
    image_url = models.URLField(blank=True, default='')
    price = models.IntegerField(default=0)
    title = models.CharField(max_length=255)
    instagram_user = models.CharField(max_length=61, blank=True, default='')
    keywords = models.ManyToManyField(Keyword)
    firebase_id = models.CharField(max_length=255, default='', blank=True, unique=True)


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
