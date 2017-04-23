from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import *
import urllib
from botocore.utils import percent_encode
from common.utils import replace_multiple
from common import utils


class Command(BaseCommand):
    def handle(self, *args, **options):
        rests = Restaurant.objects.all()
        dishes = Dish.objects.all()
        for rest in rests:
            url = urllib.parse.unquote(rest.image_url.split('?')[0])
            filename = percent_encode(utils.s3.parse(url.split('/')[-1]))
            rest.image_url = 'https://cdn.feedmeeapp.com/images/' + filename
            rest.save()
        for dish in dishes:
            url = urllib.parse.unquote(dish.image_url.split('?')[0])
            filename = percent_encode(utils.s3.parse(url.split('/')[-1]))
            dish.image_url = 'https://cdn.feedmeeapp.com/images/' + filename
            dish.save()
