import django_filters
# import rest_framework_filters as filters
import main.models as models
# https://github.com/philipn/django-rest-framework-filters


class Dish(django_filters.rest_framework.FilterSet):
    min_price = django_filters.NumberFilter(name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(name='price', lookup_expr='lte')
    keywords = django_filters.ModelMultipleChoiceFilter(
        name='keywords__word',
        to_field_name='word', conjoined=True,
        queryset=models.Keyword.objects.all())
    cuisines = django_filters.ModelMultipleChoiceFilter(
        name='restaurant__cuisines__name',
        to_field_name='name',
        queryset=models.Cuisine.objects.all())
    highlights = django_filters.ModelMultipleChoiceFilter(
        name='restaurant__highlights__name',
        to_field_name='name',
        queryset=models.Highlight.objects.all())
    has_delivery = django_filters.BooleanFilter(
        name='restaurant__delivery_provider', lookup_expr='isnull', exclude=True)
    has_booking = django_filters.BooleanFilter(
        name='restaurant__quandoo_id', lookup_expr='isnull', exclude=True)
    suburb = django_filters.ModelMultipleChoiceFilter(
        name='restaurant__suburb',
        to_field_name='suburb',
        queryset=models.Restaurant.objects.all().distinct('suburb')
    )
    order = django_filters.OrderingFilter(fields=(
        ('price', 'price'),
        ('distance', 'distance'),
    ))

    class Meta:
        model = models.Dish
        fields = ['min_price', 'max_price', 'keywords']
