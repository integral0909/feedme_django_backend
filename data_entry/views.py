from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse
from .forms import RestaurantForm, BlogForm, DishForm, RecipeForm, RecipeIngredientForm
from main.models import Restaurant, Blog, Dish, Recipe, RecipeIngredient
from django.forms import modelformset_factory, formset_factory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from common.utils import merge_dicts


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
            return HttpResponseRedirect('/data-entry/restaurants/%s/change/' % rest.id)
    # if a GET (or any other method) we'll create a blank form
    rest = get_object_or_404(Restaurant, pk=rest_id)
    context = {
        'form': RestaurantForm(instance=rest), 'tab': tab, 'action': 'Change',
        'blogs': Blog.objects.filter(restaurant=rest), 'logs': rest.get_logs(),
        'dishes': Dish.objects.filter(restaurant=rest),
        'blogform': BlogForm(initial={'restaurant_id': rest.id}),
        'dishform': DishForm(initial={'restaurant': rest}),
        'breadcrumbs': [
            {'url': '/data-entry/restaurants/', 'name': 'Restaurants'},
            {'url': '/data-entry/restaurants/%s/change/' % rest.id, 'name': rest.name}
        ]
    }
    return render(request, 'de_restaurant.html', context)


@staff_member_required
def add_restaurant(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RestaurantForm(request.POST)
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/data-entry/restaurants/%s/change/' % rest.id)
    context = {
        'form': RestaurantForm(), 'logs': [], 'tab': False, 'action': 'Add',
        'breadcrumbs': [
            {'url': '/data-entry/restaurants/', 'name': 'Restaurants'},
            {'url': '/data-entry/restaurants/add/', 'name': 'Add Restaurant'}
        ]
    }
    return render(request, 'de_restaurant.html', context)


@staff_member_required
def list_items(request, list_type):
    class_name, ObjClass, FormClass = _get_class_objects(list_type)
    paginator = Paginator(ObjClass.objects.all(), 100)
    items = _paginate(paginator, request.GET.get('page'))
    crumbs = [
        {'url': '/data-entry/%s/' % list_type, 'name': list_type.title()}
    ]
    return render(request, 'de_%s_list.html' % list_type, {list_type: items,
                                                           'breadcrumbs': crumbs})


@staff_member_required
def change_item(request, item_type, item_id=None):
    class_name, ObjClass, FormClass = _get_class_objects(item_type)
    crumbs = [
        {'url': '/data-entry/%s/' % item_type, 'name': item_type.title()},
    ]
    context = {}
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
        obj = get_object_or_404(ObjClass, pk=item_id)
        context = {'action': 'Change', 'logs': obj.get_logs(),
                   'form': FormClass(instance=obj)}
        context = merge_dicts(context, _extra_processing(item_type, obj))
        crumbs.append({
            'url': '/data-entry/%s/%s/change/' % (item_type, obj.id), 'name': str(obj)
        })
    else:
        context = merge_dicts(context, _extra_processing(item_type))
        crumbs.append({
            'url': '/data-entry/%s/add/' % item_type,
            'name': 'Add %s' % item_type.title()
        })

    defaults = {'form': FormClass(), 'breadcrumbs': crumbs, 'action': 'Add', 'logs': []}
    context = merge_dicts(defaults, context)
    return render(request, 'de_%s.html' % class_name.lower(), context)


def _extra_processing(item_type, obj=None):
    """Extra model-specific processing such as formsets for recipes."""
    ctx = {}
    if item_type == 'recipes':
        RecipeFormSet = modelformset_factory(RecipeIngredient, form=RecipeIngredientForm,
                                             exclude=('recipe', ))
        ctx['formset'] = RecipeFormSet(
            queryset=RecipeIngredient.objects.filter(recipe=obj))
    return ctx


def _get_class_objects(item_type):
    class_name = _get_classname(item_type)
    return class_name, globals()[class_name], globals()[class_name+'Form']


def _get_classname(item_type):
    """Transform pluralized name to Model name."""
    return 'Dish' if item_type == 'dishes' else item_type[:-1].title()


def _paginate(paginator, page):
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


"""
>>> from myapp.models import Author
>>> AuthorFormSet = modelformset_factory(Author, fields=('name', 'title'))
formset = AuthorFormSet(queryset=Author.objects.filter(name__startswith='O'))"""
