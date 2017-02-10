from django.core.management.base import BaseCommand
from main.models import Restaurant, Cuisine, OpeningTime, Highlight
import os
import simplejson as json


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('filepath', nargs='+', type=str)

    def handle(self, *args, **options):
        for path in options['filepath']:
            with open(path) as jdata:
                data = json.load(jdata, use_decimal=True)
                for key, item in data.items():
                    print(item, key)
                    #  refactor this whole process as a function
                    latlon = item['location']
                    offset_transformed = item['timeOffsetFromUTC']*60
                    point = 'POINT({} {})'.format(latlon[1], latlon[0])
                    restaurant = Restaurant(firebase_id=key, address=item['address'],
                                            suburb=item['suburb'], name=item['name'],
                                            image_url=item['imageURL'],
                                            information=item['information'],
                                            tripadvisor_widget=item['tripAdvisorWidget'],
                                            location=point,
                                            phone_number=item['phoneNumber'],
                                            time_offset_minutes=offset_transformed)
                    try:
                        restaurant.quandoo_id = item['quandoo_id']
                    except KeyError:
                        print('No quandoo id')
                    restaurant.save()
                    try:
                        for cuisine in item['cuisines']:
                            obj, created = Cuisine.objects.get_or_create(name=cuisine)
                            restaurant.cuisines.add(obj)
                    except KeyError:
                        print('No cuisines')
                    try:
                        #  Rewrite nested loops with map/lambda.
                        for opt in item['otherOptions']:
                            for highlight in opt.splitlines():
                                if len(highlight) == 0:
                                    continue
                                obj, created = Highlight\
                                                .objects\
                                                .get_or_create(name=highlight)
                                restaurant.highlights.add(obj)
                    except KeyError:
                        print('No highlights')
                    try:
                        for day, times in item['openingHours'].items():
                            daychoice = day.lower()[:3]
                            for time in times:
                                OpeningTime(day_of_week=daychoice, restaurant=restaurant,
                                            opens=time[0], closes=time[1])
                    except KeyError:
                        print("No opening times")
