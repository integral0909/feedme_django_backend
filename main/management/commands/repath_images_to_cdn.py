from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import *
import urllib


class Command(BaseCommand):
    def handle(self, *args, **options):
        rests = Restaurant.objects.all()
        dishes = Dish.objects.all()
        for rest in rests:
            url = urllib.parse.unquote(rest.image_url).replace(base, '').split('?')[0]
            filename = url.split('/')[-1]
            rest.image_url = 'https://cdn.feedmeeapp.com/' + filename
            rest.save()
        for dish in dishes:
            url = urllib.parse.unquote(dish.image_url).replace(base, '').split('?')[0]
            filename = url.split('/')[-1]
            dish.image_url = 'https://cdn.feedmeeapp.com/' + filename
            dish.save()
