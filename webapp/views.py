from django.shortcuts import render
from main.models import Restaurant


def restaurant_detail(request, restaurant_slug):
    restaurant = Restaurant.objects.get(slug=restaurant_slug)
    context = {'restaurant': restaurant}
    return render(request, 'restaurant.html', context)
