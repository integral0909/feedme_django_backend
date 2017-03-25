import django_filters
# import rest_framework_filters as filters
import main.models as models
# https://github.com/philipn/django-rest-framework-filters


class Dish(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(name='price', lookup_expr='lte')
    keywords = django_filters.CharFilter(name='keywords__word')
    has_delivery = django_filters.BooleanFilter(
        name='restaurant__delivery_provider', lookup_expr='isnull', exclude=True)
    has_booking = django_filters.BooleanFilter(
        name='restaurant__quandoo_id', lookup_expr='isnull', exclude=True)
    order = django_filters.OrderingFilter(fields=(
        ('price', 'price'),
        ('distance', 'distance'),
    ))

    class Meta:
        model = models.Dish
        fields = ['min_price', 'max_price', 'keywords']
