from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
import traceback
import sys

M_IN_DEGREE = 111111
# http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters


def reduce_by_distance(request, queryset):
    # http://stackoverflow.com/questions/11557182/how-to-return-a-record-with-the-lowest-distance-from-a-point-using-geodjango
    location = request.query_params.get('from_location', '').split(',')
    meters = request.query_params.get('max_distance_meters', '')
    try:
        if len(location) * len(meters) > 0:
            degrees = meters_to_degrees(meters)
            point = Point(float(location[0]), float(location[1]))
            queryset = queryset.filter(
                restaurant__location__dwithin=(
                    point, degrees
                )
            )
    except:
        print("Could not reduce by distance")
        print(sys.exc_info()[0])
    return queryset


def meters_to_degrees(meters):
    # add property test
    return float(meters) / M_IN_DEGREE
