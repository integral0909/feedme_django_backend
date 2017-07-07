from django.shortcuts import render
from main.models import Restaurant, Dish, Recipe
from django.conf import settings


def restaurant_detail(request, restaurant_slug):
    restaurant = Restaurant.objects.get(slug=restaurant_slug)
    context = {
        'restaurant': restaurant,
        'uber': settings.UBER,
        'opening_times': restaurant.get_displayable_opening_times()
    }
    return render(request, 'restaurant.html', context)


def deeplink_dish(request, dish_id):
    dish = Dish.objects.get(pk=dish_id)
    return render(request, 'deeplink_dish.html', {'dish': dish})


def deeplink_recipe(request, recipe_id):
    recipe = Recipe.objects.get(pk=recipe_id)
    return render(request, 'deeplink_recipe.html', {'recipe': recipe})


def dish_detail(request, dish_id):
    pass


dish_detail.deeplink_only = True
