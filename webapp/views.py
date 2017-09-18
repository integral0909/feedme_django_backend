from django.shortcuts import render, get_object_or_404
from django.contrib.staticfiles.templatetags.staticfiles import static
from main.models import Restaurant, Dish, Recipe, RecipeCollection
from django.conf import settings


def restaurant_detail(request, restaurant_slug):
    restaurant = Restaurant.objects.get(slug=restaurant_slug)
    context = {
        'restaurant': restaurant,
        'uber': settings.UBER,
    }
    return render(request, 'restaurant.html', context)


def deeplink_dish(request, dish_id):
    dish = Dish.objects.get(pk=dish_id)
    return render(request, 'deeplink_dish.html', {'dish': dish})


def recipe_react(request, recipe_id):
    try:
        recipe = Recipe.objects.get(pk=recipe_id)
    except Recipe.DoesNotExist:
        meta_img = static('images/og-image.jpg')
        return render(request, 'reactapp.html', {'meta_img': meta_img})
    meta_img = recipe.image_url if recipe.image_url else static('images/og-image.jpg')
    return render(request, 'react_base.html', {
        'recipe': recipe, 'app_url': 'feedmee://recipe/%s/ ' % recipe.id,
        'meta_img': meta_img, 'meta_img_alt': recipe.name, 'page_title': ' | %s' % recipe.name
    })


def recipe_collection_react(request, slug):
    try:
        collection = RecipeCollection.objects.get(slug=slug)
    except RecipeCollection.DoesNotExist:
        meta_img = static('images/og-image.jpg')
        return render(request, 'reactapp.html', {'meta_img': meta_img})
    meta_img = collection.image_url if collection.image_url else collection.recipes.first().image_url
    return render(request, 'react_base.html', {
        'page_title': ' | %s' % collection.name, 'meta_img': meta_img,
        'meta_img_alt': collection.name
    })


def react_app(request):
    meta_img = static('images/og-image.jpg')
    return render(request, 'react_base.html', {'meta_img': meta_img})


def dish_detail(request, dish_id):
    dish = get_object_or_404(Dish, pk=dish_id)
    meta_img = dish.image_url if dish.image_url else static('images/og-image.jpg')
    return render(request, 'dish.html',
        {'dish': dish, 'app_url': 'feedmee://dish/%s/ ' % dish.id, 'meta_img': meta_img,
        'meta_img_alt': dish.title, 'page_title': ' | %s' % dish.title,
         'uber': settings.UBER,}
    )
