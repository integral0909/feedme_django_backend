from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

M_IN_DEGREE = 111111


def reduce_by_distance(request, queryset):
    location = request.query_params.get('from_location', []).split(',')
    meters = request.query_params.get('max_distance_meters', '')
    degrees = meters_to_degrees(meters)
    if len(location) * len(meters) > 0:
        point = Point(float(location[0]), float(location[1]))
        queryset = queryset.filter(
            restaurant__location__dwithin=(
                point, degrees
            )
        )
    return queryset


def meters_to_degrees(meters):
    return float(meters) / M_IN_DEGREE
