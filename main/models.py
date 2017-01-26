from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    bio = models.TextField(blank=True)
    country = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
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
    author = models.CharField(max_length=255)
    image_url = models.URLField()
    title = models.CharField(max_length=255)
    url = models.URLField()


class Dish(Creatable):
    restaurant = models.ForeignKey('Restaurant', models.CASCADE)
    image_url = models.URLField()
    price = models.IntegerField(default=0)
    title = models.CharField(max_length=255)
    instagram_user = models.URLField()
    keywords = models.ManyToManyField('DishKeyword', models.DO_NOTHING)


class Keyword(models.Model):
    word = models.CharField(max_length=255)


class Feedback(models.Model):
    pass


class Profile(models.Model):
    first


class Restaurant(models.Model):
    pass


class Report(models.Model):
    """
    A report is a statement a user might make about the accuracy of restaurant data.
    """
    pass
