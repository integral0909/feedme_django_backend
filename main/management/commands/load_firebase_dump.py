from django.core.management.base import BaseCommand
from main.models import Restaurant, Cuisine, OpeningTime, Highlight, Dish, Keyword
from main.lib.firebase_loaders import *
import os
import simplejson as json


def load_restaurant(key, item):
    restaurant = save_restaurant(item, key)
    save_manytomany(restaurant, item.get('cuisines', []), 'Cuisine', 'name')
    for opt in item.get('otherOptions', []):
        highlights = opt.replace('"', '').splitlines()
        save_manytomany(restaurant, highlights, 'Highlight', 'name')
    for day, times in item.get('openingHours', {}).items():
        for time in times:
            opens = int_to_time(time[0] + (item['timeOffsetFromUTC']*60*60))
            closes = int_to_time(time[1] + (item['timeOffsetFromUTC']*60*60))
            OpeningTime(day_of_week=day.lower()[:3], restaurant=restaurant,
                        opens=opens, closes=closes).save()


def load_dish(key, item):
    dish = save_dish(item, key)
    save_manytomany(dish, item.get('keywords', {}), 'Keyword', 'word')


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
