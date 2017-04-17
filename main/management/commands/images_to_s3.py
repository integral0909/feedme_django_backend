from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from main.models import *
from main.management.commands.load_firebase_dump import run_chunked_iter
import pyrebase
import urllib
import wget
import boto3
import time

base = 'https://firebasestorage.googleapis.com/v0/b/feedmee-appsppl-dev.appspot.com/o/'
s3_client = boto3.client('s3')
config = {
  "apiKey": "AIzaSyDJdcBZSwLlpWENN5oWZYQVZL0u7ZPSzhc",
  "authDomain": "feedmee-appsppl-dev.firebaseapp.com",
  "databaseURL": "https://feedmee-appsppl-dev.firebaseio.com",
  "storageBucket": "feedmee-appsppl-dev.appspot.com",
}
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()


def _download_imgs(rests):
    for rest in rests:
        dl_url = urllib.parse.unquote(rest.image_url).replace(base, '').split('?')[0]
        filename = dl_url.split('/')[-1]
        try:
            if dl_url[:6] in ['images', 'websit']:
                storage.child(dl_url).download(settings.TMP_PATH + filename)
            elif dl_url[:4] == 'http':
                wget.download(dl_url, settings.TMP_PATH + filename)
        except ValueError:
            print('URL invalid', dl_url)
        except:
            print('Unknown error')
        else:
            time.sleep(0.1)
            try:
                s3_client.upload_file(settings.TMP_PATH + filename, 'fdme-raw-img',
                                      filename)
            except FileNotFoundError:
                time.sleep(1)
                s3_client.upload_file(settings.TMP_PATH + filename, 'fdme-raw-img',
                                      filename)


class Command(BaseCommand):
    def handle(self, *args, **options):
        rests = Restaurant.objects.all()
        dishes = Dish.objects.all()
        run_chunked_iter(rests, _download_imgs)
        run_chunked_iter(dishes, _download_imgs)
