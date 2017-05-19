from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import *
import urllib
from botocore.utils import percent_encode
from common import utils


class Command(BaseCommand):
    def handle(self, *args, **options):
        rests = Restaurant.objects.all()
        dishes = Dish.objects.all()
        utils.async.run_chunked_iter(rests, _worker)
        utils.async.run_chunked_iter(dishes, _worker)


def _worker(obj_collection):
    for obj in obj_collection:
        url = urllib.parse.unquote(obj.image_url.split('?')[0])
        filename = filename_from_url(url)
        obj.image_url = 'https://cdn.feedmeeapp.com/images/' + filename
        obj.save()


def filename_from_url(url):
    filename = utils.s3.parse(url.split('/')[-1])
    return '%s.jpg' % utils.numbers_only(filename.split('%')[0])

