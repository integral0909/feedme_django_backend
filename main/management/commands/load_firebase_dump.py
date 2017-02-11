from django.core.management.base import BaseCommand
from main.models import Restaurant, Cuisine, OpeningTime, Highlight
from main.lib.firebase_loaders import *
import os
import simplejson as json


def load_restaurant(key, item):
    restaurant = save_restaurant(item, key)
    save_manytomany(restaurant, item.get('cuisines', []), 'Cuisine', 'name')
    for opt in item.get('otherOptions', []):
        save_manytomany(restaurant, opt.splitlines(), 'Highlight', 'name')
    for day, times in item.get('openingHours', {}).items():
        for time in times:
            OpeningTime(day_of_week=day.lower()[:3], restaurant=restaurant,
                        opens=time[0], closes=time[1])


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('table', nargs='+', type=str)
        parser.add_argument('filepath', nargs='+', type=str)

    def handle(self, *args, **options):
        for idx, path in enumerate(options['filepath']):
            with open(path) as jdata:
                data = json.load(jdata, use_decimal=True)
                for key, item in data.items():
                    globals()['load_{}'.format(options['table'][idx])](key, item)
