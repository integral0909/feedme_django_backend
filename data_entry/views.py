from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse
from .forms import RestaurantForm, BlogForm, DishForm
from main.models import Restaurant, Blog, Dish, Recipe
from django.forms import modelformset_factory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@staff_member_required
def change_restaurant(request, rest_id=None, tab=False):
    # if this is a POST request we need to process the form data
    crumbs = [
        {'url': '/data-entry/restaurants/', 'name': 'Restaurants'}
    ]
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RestaurantForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        try:
            rest = Restaurant.objects.get(pk=rest_id)
        except Restaurant.DoesNotExist:
            form = RestaurantForm()
            blogs = []
        else:
            form = RestaurantForm(instance=rest)
            blogs = Blog.objects.filter(restaurant=rest)
            dishes = Dish.objects.filter(restaurant=rest)
            crumbs.append({
                'url': '/data-entry/restaurants/%s/change/' % rest.id, 'name': rest.name
            })

    context = {
        'form': form, 'blogform': BlogForm(), 'blogs': blogs, 'dishes': dishes,
        'dishform': DishForm(), 'breadcrumbs': crumbs, 'tab': tab
    }
    return render(request, 'de_restaurant.html', context)


@staff_member_required
def list_items(request, list_type):
    class_name = 'Dish' if list_type == 'dishes' else list_type[:-1].title()
    rest_list = globals()[class_name].objects.all()
    paginator = Paginator(rest_list, 100)

    page = request.GET.get('page')
    try:
        rests = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        rests = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        rests = paginator.page(paginator.num_pages)
    crumbs = [
        {'url': '/data-entry/%s/' % list_type, 'name': list_type.title()}
    ]
    return render(request, 'de_%s_list.html' % list_type, {list_type: rests,
                                                           'breadcrumbs': crumbs})
