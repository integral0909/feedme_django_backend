import operator
import django_filters
# import rest_framework_filters as filters
from past.builtins import reduce

import main.models as models
from django.db.models.query import QuerySet
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity


def fuzzy_string_match(queryset, name, value):
    return queryset.annotate(
        similarity=TrigramSimilarity(name, value)
    ).filter(similarity__gte=0.1).order_by('-similarity')


class Dish(django_filters.rest_framework.FilterSet):
    min_price = django_filters.NumberFilter(name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(name='price', lookup_expr='lte')
    keywords = django_filters.ModelMultipleChoiceFilter(
        name='keywords__word',
        to_field_name='word',  # conjoined=True, Removed until ui limit 3 enforced
        queryset=models.Keyword.objects.all())
    cuisines = django_filters.ModelMultipleChoiceFilter(
        name='restaurant__cuisines__name',
        to_field_name='name',
        queryset=models.Cuisine.objects.all())
    highlights = django_filters.ModelMultipleChoiceFilter(
        name='restaurant__highlights__name',
        to_field_name='name',
        queryset=models.Highlight.objects.all())
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name', to_field_name='name',
        queryset=models.Tag.objects.all())
    has_delivery = django_filters.BooleanFilter(
        name='restaurant__delivery_provider', lookup_expr='isnull', exclude=True)
    has_booking = django_filters.BooleanFilter(
        name='restaurant__quandoo_id', lookup_expr='isnull', exclude=True)
    suburb = django_filters.ModelMultipleChoiceFilter(
        name='restaurant__suburb', to_field_name='suburb',
        queryset=models.Restaurant.objects.all().distinct('suburb')
    )
    order = django_filters.OrderingFilter(fields=(
        ('price', 'price'),
        ('distance', 'distance'),
    ))

    class Meta:
        model = models.Dish
        fields = ['min_price', 'max_price', 'keywords']


class Recipe(django_filters.rest_framework.FilterSet):
    min_total_time = django_filters.NumberFilter(name='total_time_seconds',
                                                 lookup_expr='gte')
    max_total_time = django_filters.NumberFilter(name='total_time_seconds',
                                                 lookup_expr='lte')
    keywords = django_filters.ModelMultipleChoiceFilter(
        name='keywords__word',
        to_field_name='word',  # conjoined=True, Removed until ui limit 3 enforced
        queryset=models.Keyword.objects.all())
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name', to_field_name='name',
        queryset=models.Tag.objects.all())
    difficulty = django_filters.MultipleChoiceFilter(
        choices=models.Recipe.DIFFICULTY_CHOICES
    )
    ingredients = django_filters.ModelMultipleChoiceFilter(
        name='ingredients__ingredient__name',
        to_field_name='name', conjoined=True,
        queryset=models.Ingredient.objects.all(),
        method='ingredient_search'
    )

    def ingredient_search(self, qs, name, value):
        if isinstance(value, QuerySet) and value.count():
            query = reduce(operator.or_, (Q(ingredients__ingredient__name__icontains=v.name) for v in value))
            return qs.filter(query)
        elif value:
            kwargs = {'%s__icontains' % name: value}
            return qs.filter(**kwargs)
        else:
            return qs

    class Meta:
        model = models.Recipe
        fields = ['min_total_time', 'max_total_time', 'keywords', 'tags', 'difficulty']


class Ingredient(django_filters.rest_framework.FilterSet):
    search = django_filters.CharFilter(
        name='name', method=fuzzy_string_match
    )
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = models.Ingredient
        fields = ['name', 'description']
