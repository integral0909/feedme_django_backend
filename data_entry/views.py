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
def list_items(request, item_type):
    class_name, ObjClass, FormClass = _get_class_objects(item_type)
    paginator = Paginator(ObjClass.objects.all(), 100)
    items = _paginate(paginator, request.GET.get('page'))
    return render(request, 'de_%s_list.html' % item_type, {item_type: items})


@staff_member_required
def change_item(request, item_type, item_id=None, tab=False):
    class_name, ObjClass, FormClass = _get_class_objects(item_type)
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
        context = merge_dicts({'action': 'Change', 'form': FormClass(instance=obj),
                               'logs': obj.get_logs()}, _extra_processing(item_type, obj))
    else:
        context = _extra_processing(item_type)

    defaults = {'form': FormClass(), 'action': 'Add', 'logs': [], 'tab': tab}
    context = merge_dicts(defaults, context)
    return render(request, 'de_%s.html' % class_name.lower(), context)


def _extra_processing(item_type, obj=None):
    """Extra model-specific processing such as formsets for recipes."""
    ctx = {}
    if item_type == 'recipes' or (item_type == 'restaurants' and obj):
        RecipeFormSet = modelformset_factory(RecipeIngredient, form=RecipeIngredientForm,
                                             exclude=('recipe', ))
    if item_type == 'recipes':
        ctx['formset'] = RecipeFormSet(
            queryset=RecipeIngredient.objects.filter(recipe=obj))
    if item_type == 'restaurants' and obj:
        dishes = Dish.objects.filter(restaurant=obj)
        ctx = {
            'blogs': Blog.objects.filter(restaurant=obj),
            'dishes': dishes,
            'blogform': BlogForm(initial={'restaurant_id': obj.id}),
            'dishform': DishForm(initial={'restaurant': obj}),
            'recipeformset': RecipeFormSet(queryset=Recipe.objects.none()),
            'recipeform': RecipeForm(dish_opts=dishes.filter(recipe__isnull=True)),
            'recipes': Recipe.objects.filter(dishes__restaurant=obj)
        }
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
