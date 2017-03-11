from django.contrib.auth.models import User, Group
from django.db.models import Count, Sum
from rest_framework import viewsets, generics, pagination
from rest_framework.views import APIView
from rest_framework.response import Response
import api.serializers as serializers
import main.models as models
import api.filters as filters
import api.lib.custom_filters as custom_filters


class LargeResultsSetPagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = serializers.User


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = serializers.Group


class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = models.Restaurant.objects.all()
    serializer_class = serializers.Restaurant


class DishViewSet(viewsets.ModelViewSet):
    queryset = models.Dish.objects.all()
    serializer_class = serializers.Dish
    filter_class = filters.Dish

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if self.request.query_params.get('saved') == 'true':
            queryset = models.Dish.objects.filter(likes__user=self.request.user)
        else:
            queryset = custom_filters.reduce_by_distance(request, queryset)
            queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(convertedSet, many=True)
        return Response(serializer.data)


class DeliveryProviderViewSet(viewsets.ModelViewSet):
    queryset = models.DeliveryProvider.objects.all()
    serializer_class = serializers.DeliveryProvider


class LikesList(APIView):
    """
    Post only, for saving likes

    * Requires token authentication.
    """
    def post(self, request, format=None):
        try:
            user = request.user
            did_like = request.data.get("did_like")
            dish = models.Dish.objects.get(pk=request.data.get("dish_id"))
            like = models.Like.objects.get(dish=dish, user=user)
            like.did_like = did_like
            like.save()
            return Response({"success": True, "created": False})
        except models.Like.DoesNotExist:
            like = models.Like(user=user, dish=dish, did_like=did_like)
            like.save()
            return Response({"success": True, "created": True})
        except models.Dish.DoesNotExist:
            return Response({"success": False, "created": False,
                             "Error": "Dish not found"}, 400)
