from main.models import Restaurant, Cuisine, Highlight


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


def save_manytomany(parent, list, mtm_class_name, prop_name):
    mtm_class = globals()[mtm_class_name]
    mtm_name = mtm_class_name.lower()+'s'
    params = {}
    for new_item in list:
        if len(new_item) > 0:
            params[prop_name] = new_item
            obj, created = mtm_class.objects.get_or_create(**params)
            getattr(parent, mtm_name).add(obj)
