from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse
from .forms import RestaurantForm, BlogForm, DishForm, RecipeForm
from main.models import Restaurant, Blog, Dish, Recipe
from django.forms import modelformset_factory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType


@staff_member_required
def change_restaurant(request, rest_id=None, tab=False):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RestaurantForm(request.POST)
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')
    # if a GET (or any other method) we'll create a blank form
    try:
        rest = Restaurant.objects.get(pk=rest_id)
    except Restaurant.DoesNotExist:
        return HttpResponseRedirect('/data-entry/restaurants/add/')

    form = RestaurantForm(instance=rest)
    blogs = Blog.objects.filter(restaurant=rest)
    dishes = Dish.objects.filter(restaurant=rest)
    logs, logCount = rest.get_logs()

    context = {
        'form': form, 'blogs': blogs, 'dishes': dishes, 'tab': tab, 'action': 'Change',
        'blogform': BlogForm(initial={'restaurant_id': rest.id}),
        'dishform': DishForm(initial={'restaurant': rest}),
        'breadcrumbs': [
            {'url': '/data-entry/restaurants/', 'name': 'Restaurants'},
            {'url': '/data-entry/restaurants/%s/change/' % rest.id, 'name': rest.name}
        ],
        'logs': logs, 'logCount': logCount
    }
    return render(request, 'de_restaurant.html', context)


@staff_member_required
def add_restaurant(request):
    form = RestaurantForm()
    logs, logCount = [], 0

    context = {
        'form': form, 'logs': logs, 'logCount': logCount, 'tab': False, 'action': 'Add',
        'breadcrumbs': [
            {'url': '/data-entry/restaurants/', 'name': 'Restaurants'},
            {'url': '/data-entry/restaurants/add/', 'name': 'Add Restaurant'}
        ]
    }
    return render(request, 'de_restaurant.html', context)


@staff_member_required
def list_items(request, list_type):
    class_name = _get_classname(list_type)
    rest_list = globals()[class_name].objects.all()
    paginator = Paginator(rest_list, 100)

    page = request.GET.get('page')
    try:
        rests = paginator.page(page)
    except PageNotAnInteger:
        rests = paginator.page(1)
    except EmptyPage:
        rests = paginator.page(paginator.num_pages)
    crumbs = [
        {'url': '/data-entry/%s/' % list_type, 'name': list_type.title()}
    ]
    return render(request, 'de_%s_list.html' % list_type, {list_type: rests,
                                                           'breadcrumbs': crumbs})


@staff_member_required
def change_item(request, item_type, item_id=None):
    class_name = _get_classname(item_type)
    ObjClass = globals()[class_name]
    FormClass = globals()[class_name+'Form']
    crumbs = [
        {'url': '/data-entry/%s/' % item_type, 'name': item_type.title()},
    ]
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = FormClass(request.POST)
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/data-entry/%s/%s/change/' % (item_type,
                                                                       item_id))
    # if a GET (or any other method) we'll create a blank form
    if item_id:
        try:
            obj = ObjClass.objects.get(pk=item_id)
        except ObjClass.DoesNotExist:
            return HttpResponseRedirect('/data-entry/%s/add/' % item_type)
        else:
            form = FormClass(instance=obj)
            logs, logCount = obj.get_logs()
            crumbs.append({
                'url': '/data-entry/%s/%s/change/' % (item_type, obj.id),
                'name': str(obj)
            })
            action = 'Change'
    else:
        form = FormClass()
        logs, logCount = [], 0
        crumbs.append({
            'url': '/data-entry/%s/add/' % item_type,
            'name': 'Add %s' % item_type.title()
        })
        action = 'Add'

    context = {'form': form, 'breadcrumbs': crumbs, 'logs': logs, 'logCount': logCount,
               'action': action}
    return render(request, 'de_%s.html' % class_name.lower(), context)


def _get_classname(item_type):
    """Transform pluralized name to Model name."""
    return 'Dish' if item_type == 'dishes' else item_type[:-1].title()
