from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from .forms import (RestaurantForm, BlogForm, DishForm, RecipeForm, RecipeIngredientForm,
                    HighlightForm, TagForm, CuisineForm, RestaurantOpeningTimeForm)
from main.models import (Restaurant, Blog, Dish, Recipe, RecipeIngredient,
                         Highlight, Tag, Cuisine, OpeningTime)
from django.forms import modelformset_factory, formset_factory, inlineformset_factory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from common.utils import merge_dicts


@staff_member_required
def list_items(request, item_type):
    class_name, ObjClass, FormClass = _get_class_objects(item_type)
    paginator = Paginator(ObjClass.objects.all().order_by('-id'), 100)
    items = _paginate(paginator, request.GET.get('page'))
    return render(request, 'de_%s_list.html' % item_type, {item_type: items})


@staff_member_required
def change_item(request, item_type, item_id=None, tab=False):
    class_name, ObjClass, FormClass = _get_class_objects(item_type)
    if item_id:
        obj = get_object_or_404(ObjClass, pk=item_id)
        context = merge_dicts({'action': 'Change', 'form': FormClass(instance=obj),
                               'logs': obj.get_logs()}, _extra_processing(item_type, obj))
    else:
        context = _extra_processing(item_type)

    if request.method == 'POST':
        return _change_item_post(request, item_id, obj, FormClass, context, item_type)

    defaults = {'form': FormClass(), 'action': 'Add', 'logs': [], 'tab': tab}
    context = merge_dicts(defaults, context)
    return render(request, 'de_%s.html' % class_name.lower(), context)


def _change_item_post(request, item_id, obj, FormClass, context, item_type):
    """All logic unique to handling a POST request for change_item."""
    form, FLAG = _update_or_insert(item_id, FormClass, obj, request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        try:
            formset = context['OTFormset'](request.POST, instance=obj)
        except KeyError:
            obj.save()
        else:
            if formset.is_valid():
                obj.save()
                formset.save()
        finally:
            form.save_m2m()
            return _change_item_post_success(request, obj, FLAG, item_type)
    else:
        context['form'] = form
        return render(request, 'de_%s.html' % class_name.lower(), context)


def _change_item_post_success(request, obj, FLAG, item_type):
    _log_entry(request, obj, FLAG)
    return HttpResponseRedirect('/data-entry/%s/%s/change/' % (item_type, obj.id))


def _update_or_insert(item_id, FormClass, obj, POST):
    if item_id:
        form = FormClass(POST, instance=obj)
        FLAG = CHANGE
    else:
        form = FormClass(POST)
        FLAG = ADDITION
    return form, FLAG


@staff_member_required
def modal(request, modal):
    """Modal only returns an empty form or handles a save. Cannot edit."""
    basic = request.GET.get('basic')
    class_name, ObjClass, FormClass = _get_class_objects(modal)
    template = 'modals/basic.html' if basic else 'modals/%s.html' % modal
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            obj = form.save()
            _log_entry(request, obj, ADDITION)
            template = 'modals/success.html'
            return render(request, template, {'obj': obj})
    else:
        form = FormClass()
    return render(request, template, {'form': form, 'modal': modal})


@staff_member_required
def async_form(request, item_type):
    """
    Handles forms submitted asynchronously.

    This assumes that a successful save will not redirect.
    Instead return an empty form ready for a new submission
    """
    class_name, ObjClass, FormClass = _get_class_objects(item_type)
    if request.method == 'POST':
        form = FormClass(request.POST)
        FLAG = ADDITION
        if form.data.get('id'):
            obj = get_object_or_404(ObjClass, pk=form.data.get('id'))
            form = FormClass(request.POST, instance=obj)
            FLAG = CHANGE
        if form.is_valid():
            obj = form.save()
            _log_entry(request, obj, FLAG)
            if item_type == 'dishes':
                form = FormClass(initial={'restaurant': obj.restaurant})
            elif item_type == 'blogs':
                form = FormClass(initial={
                    'restaurant_id': form.data.get('restaurant_id')
                })
            elif item_type is not 'restaurants':
                form = FormClass()
        else:
            print(form.errors)
        return render(request, 'de_%sform.html' % class_name.lower(), merge_dicts(
                      {'form': form, 'async': True}, _extra_processing(item_type)))
    else:
        return HttpResponseBadRequest()


@staff_member_required
def async_formset(request, item_type):
    class_name, ObjClass, FormClass = _get_class_objects(item_type)
    context = {}
    if request.method == 'POST':
        FormsetClass = modelformset_factory(ObjClass, form=FormClass,
                                            can_delete=True)
        formset = FormsetClass(request.POST)


def _log_entry(request, obj, FLAG):
    LogEntry.objects.log_action(
        user_id=request.user.pk, object_id=obj.id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_repr=str(obj), action_flag=FLAG
    )


def _extra_submit_processing(item_type):
    if item_type == 'recipe':
        pass  # Set dishes and formset


def _extra_processing(item_type, obj=None):
    """Extra model-specific processing such as formsets for recipes."""
    ctx = {}
    if item_type == 'recipes' or (item_type == 'restaurants' and obj):
        RecipeFormSet = modelformset_factory(RecipeIngredient, form=RecipeIngredientForm,
                                             can_delete=True)
    if item_type == 'recipes':
        ctx['formset'] = RecipeFormSet(
            queryset=RecipeIngredient.objects.filter(recipe=obj))
    if item_type == 'restaurants' and obj:
        dishes = Dish.objects.filter(restaurant=obj)
        OTFormset = inlineformset_factory(Restaurant, OpeningTime,
                                          form=RestaurantOpeningTimeForm)
        otfset = OTFormset(instance=obj)
        ctx = {
            'blogs': Blog.objects.filter(restaurant=obj),
            'dishes': dishes,
            'blogform': BlogForm(initial={'restaurant_id': obj.id}),
            'dishform': DishForm(initial={'restaurant': obj}),
            'recipeformset': RecipeFormSet(queryset=Recipe.objects.none()),
            'recipeform': RecipeForm(dish_opts=dishes.filter(recipe__isnull=True)),
            'recipes': Recipe.objects.filter(dishes__restaurant=obj),
            'otfset': otfset,
            'OTFormset': OTFormset
        }
    return ctx


def _get_class_objects(item_type):
    """Returns the class name, class, and form class for a given item_type."""
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
