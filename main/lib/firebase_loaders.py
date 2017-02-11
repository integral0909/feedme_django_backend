from main.models import Restaurant, Cuisine, Highlight, Dish, Keyword
import datetime
from django.utils.text import slugify


def int_to_time(seconds):
    hours = abs(int(seconds / 3600)) % 24
    mins = abs(int((seconds % 3600) / 60))
    sec = abs(int((seconds % 3600) % 60))
    return datetime.time(hours, mins, sec)


def save_restaurant(item, key):
    point = 'POINT({} {})'.format(item['location'][1], item['location'][0])
    params = {
        'firebase_id': key, 'address': item['address'],
        'suburb': item['suburb'], 'name': item['name'],
        'image_url': item['imageURL'], 'information': item['information'],
        'tripadvisor_widget': item['tripAdvisorWidget'],
        'location': point, 'phone_number': item['phoneNumber'],
        'time_offset_minutes': item['timeOffsetFromUTC']*60,
        'quandoo_id': item.get('quandoo_id', None)
    }
    restaurant, created = Restaurant.objects.update_or_create(**params)
    return restaurant


def save_dish(item, key):
    restaurant = Restaurant.objects.get(firebase_id=item['_restaurant'])
    params = {
        'firebase_id': key, 'restaurant': restaurant, 'title': item['title'],
        'price': int(item['price']*100), 'image_url': item['imageURL'],
        'instagram_user': item.get('instagramUser', '')
    }
    dish, created = Dish.objects.update_or_create(**params)
    return dish


def save_manytomany(parent, list, mtm_class_name, prop_name):
    mtm_class = globals()[mtm_class_name]
    mtm_name = mtm_class_name.lower()+'s'
    params = {}
    defaults = {}
    for new_item in list:
        if len(new_item) > 1:
            params[prop_name] = new_item
            if hasattr(mtm_class, 'slug'):
                params['slug'] = slugify(new_item)
                del params[prop_name]
                defaults[prop_name] = new_item
            obj, created = mtm_class.objects.get_or_create(defaults=defaults, **params)
            getattr(parent, mtm_name).add(obj)
