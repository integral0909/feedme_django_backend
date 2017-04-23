from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Restaurant, Cuisine, OpeningTime, Highlight, Dish, Keyword
from main.lib.firebase_loaders import *
import threading
import os
import simplejson as json


def load_delivery_provider(key, item):
    delprov = save_delivery_provider(item, key)


def load_restaurants(key, item):
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


def load_dishes(key, item):
    dish = save_dish(item, key)
    save_manytomany(dish, item.get('keywords', {}), 'Keyword', 'word')


def load_blogs(key, item):
    blog = save_blog(item, key)


def load_restaurant_blogs(key, item):
    try:
        restaurant = Restaurant.objects.get(firebase_id=key)
        for blog_fbase_id in item:
            blog = Blog.objects.get(firebase_id=blog_fbase_id)
            restaurant.blogs.add(blog)
    except Restaurant.DoesNotExist:
        print("Restaurant does not exist:", key)


def load_users(key, item):
    user = save_user(item, key)


def load_likes(key, item):
    like = save_like(item, key)


def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]


def run_chunked_iter(iterable_item, worker_func, args=None, num_threads=8):
    """
    Split the provided iterable into chunks, process each chunk in a separate thread
    """
    threads = []
    chunked_iterables = chunkify(iterable_item, num_threads)
    for chunk in chunked_iterables:
        main_args = [chunk]
        if isinstance(args, (list, tuple, set)) is True:
            main_args = main_args + list(args)
        t = threading.Thread(target=worker_func, args=main_args)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


def worker(chunk, func):
    for key, item in chunk:
        func(key, item)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('table', nargs='+', type=str)
        parser.add_argument('filepath', nargs='+', type=str)

    def handle(self, *args, **options):
        path = options['filepath'][0]
        with open(path) as jdata:
            data = json.load(jdata, use_decimal=True)
            func = globals()['load_{}'.format(options['table'][0])]
            run_chunked_iter(list(data.items()), worker, args=(func, ))
