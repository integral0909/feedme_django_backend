from django.shortcuts import render
from main.models import Restaurant
from django.conf import settings


def restaurant_detail(request, restaurant_slug):
    restaurant = Restaurant.objects.get(slug=restaurant_slug)
    context = {
        'restaurant': restaurant,
        'uber': settings.UBER,
        'opening_times': restaurant.get_displayable_opening_times()
    }
    return render(request, 'restaurant.html', context)
