from main.models import (Restaurant, Cuisine, Highlight, Dish, Keyword, Blog, Profile,
                         Like, DeliveryProvider)
import datetime
from urllib.parse import urlparse
from django.utils.text import slugify
from django.contrib.auth.models import User


def int_to_time(seconds):
    hours = abs(int(seconds / 3600)) % 24
    mins = abs(int((seconds % 3600) / 60))
    sec = abs(int((seconds % 3600) % 60))
    return datetime.time(hours, mins, sec)


def save_delivery_provider(item, key):
    params = {'slug': key}
    defaults = {
        'name': item.get('name'),
        'logo_url': item.get('logo'),
        'title': item.get('title'),
        'description': item.get('description', '')
    }
    del_prov, created = DeliveryProvider.objects.update_or_create(defaults=defaults,
                                                                  **params)
    return del_prov


def save_restaurant(item, key):
    point = 'POINT({} {})'.format(item['location'][1], item['location'][0])
    try:
        delivery_provider = DeliveryProvider.objects.get(
            slug=item.get('delivery_type', item.get('delivery_provider'))
        )
    except DeliveryProvider.DoesNotExist:
        delivery_provider = None
    params = {'firebase_id': key}
    defaults = {
        'address': item['address'],
        'suburb': item['suburb'], 'name': item['name'],
        'image_url': item['imageURL'], 'information': item['information'],
        'tripadvisor_widget': item['tripAdvisorWidget'],
        'location': point, 'phone_number': item['phoneNumber'],
        'time_offset_minutes': item['timeOffsetFromUTC']*60,
        'quandoo_id': item.get('quandoo_id', None),
        'delivery_link': item.get('delivery_link'),
        'delivery_provider': delivery_provider
    }
    restaurant, created = Restaurant.objects.update_or_create(defaults=defaults, **params)
    return restaurant


def save_dish(item, key):
    restaurant = Restaurant.objects.get(firebase_id=item['_restaurant'])
    instagram_user = item.get('instagramUser', '').replace('@', '')
    if 'instagram.com' in instagram_user:
        insta_url = urlparse(instagram_user)
        instagram_user = insta_url.path.replace('/', '')
    if len(instagram_user) > 61:
        instagram_user = ''
    params = {'firebase_id': key}
    defaults = {
        'restaurant': restaurant, 'title': item['title'],
        'price': int(item['price']*100), 'image_url': item['imageURL'],
        'instagram_user': instagram_user
    }
    dish, created = Dish.objects.update_or_create(defaults=defaults, **params)
    return dish


def save_blog(item, key):
    params = {'firebase_id': key}
    defaults = {
        'author': item.get('author', ''),
        'image_url': item.get('imageURL', ''), 'title': item.get('title', ''),
        'url': item.get('url', '')
    }
    blog, created = Blog.objects.update_or_create(defaults=defaults, **params)
    return blog


def save_user(item, key):
    try:
        user = User.objects.get(profile__firebase_id=key)
    except User.DoesNotExist:
        try:
            pdata = item['providerData'][0]
        except KeyError:
            return False
        params = {
            'email': pdata.get('email', '')[:254],
            'username': pdata.get('uid', pdata.get('email', ''))[:150],
            'first_name': item.get('firstname', '')[:30],
            'last_name': item.get('lastname', '')[:30],
        }
        user = User(**params)
        user.save()
        save_profile(pdata, key, user).save()
    return user


def save_profile(pdata, key, user):
    profile = Profile(provider=pdata['providerID'], firebase_id=key, user=user)
    if pdata['providerID'] == 'facebook.com':
        profile.fb_id = pdata['uid']
        profile.photo_url = pdata.get('photoURL', '')
    return profile


def save_like(item, key):
    for junk_key, dish_item in item.items():
        # print(dish_item, junk_key)
        try:
            dish = Dish.objects.get(firebase_id=dish_item['_dish'])
            user = User.objects.get(profile__firebase_id=dish_item['_user'])
            like, created = Like.objects.update_or_create(
                dish=dish, user=user, defaults={'did_like': dish_item['didLike']}
            )
            return like
        except Dish.DoesNotExist:
            print('Dish Does not exist:', dish_item['_dish'])
        except User.DoesNotExist:
            print('User Does not exist:', dish_item['_user'])
        except Like.MultipleObjectsReturned:
            print('Multiple Likes exist for this User/Dish.')
        except TypeError:
            print('Type error: {}\nKey: {}'.format(dish_item, junk_key))
            continue


def save_manytomany(parent, list, mtm_class_name, prop_name):
    """
    Save a list of items from Firebase as a many to many in Django.

    parent: The parent object, i.e. an instance of Restaurant
    list: The list from Firebase
    mtm_class_name: The name of the class in a ManyToMany relationship, i.e. Highlight
    prop_name: The name of the primary property used to get/save objects, i.e. name.

    This function also checks for the existence of a similar object via slug.
    This prevents duplicates arising from different capitalisations.

    Note: This function only works with Firebase lists of strings to be
          transformed into django objects.
    """
    mtm_class = globals()[mtm_class_name]
    mtm_name = mtm_class_name.lower()+'s'
    params = {}
    defaults = {}
    max_length = mtm_class._meta.get_field(prop_name).max_length
    for new_item in list:
        if len(new_item) > 1:
            new_item_trimmed = new_item[:max_length]
            params[prop_name] = new_item_trimmed
            if hasattr(mtm_class, 'slug'):
                params['slug'] = slugify(new_item_trimmed)
                del params[prop_name]
                defaults[prop_name] = new_item_trimmed
            obj, created = mtm_class.objects.get_or_create(defaults=defaults, **params)
            getattr(parent, mtm_name).add(obj)
