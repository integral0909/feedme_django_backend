from datetime import datetime, timedelta, timezone
from django.contrib.auth.models import User, Group
from django.db.models import Count, Sum
from rest_framework import viewsets, generics, pagination
from rest_framework.views import APIView
from rest_framework.response import Response
import api.serializers as serializers
import main.models as models
import api.filters as filters
import api.lib.custom_filters as custom_filters

INIT_DONATIONS = 1834


class LargeResultsSetPagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100


class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = models.Restaurant.objects.all()
    serializer_class = serializers.Restaurant


class DishViewSet(viewsets.ModelViewSet):
    queryset = models.Dish.objects.all()
    serializer_class = serializers.Dish
    filter_class = filters.Dish

    def list(self, request, *args, **kwargs):
        if self.request.query_params.get('saved') == 'true':
            queryset = models.Dish.objects.saved(self.request.user).distinct('id')
        else:
            queryset = self.filter_queryset(self.get_queryset().reduce_by_distance(
                location=request.query_params.get('from_location', '').split(','),
                meters=request.query_params.get('max_distance_meters', '')
            ).not_liked(self.request.user).fresh(self.request.user)
             .order_by('random', 'id').distinct('random', 'id'))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(convertedSet, many=True)
        return Response(serializer.data)


class RestaurantDishesViewSet(generics.ListAPIView):
    """
    Dishes from a particular restaurant

    Reference: http://stackoverflow.com/questions/17337843/how-to-implement-a-hierarchy-of-resources-eg-parents-id-children-in-django
    """
    queryset = models.Dish.objects.all()
    serializer_class = serializers.Dish
    filter_class = filters.Dish

    def get_queryset(self):
        rest_pk = self.kwargs['restaurant_pk']
        return self.queryset.filter(restaurant__pk=rest_pk)


class DeliveryProviderViewSet(viewsets.ModelViewSet):
    queryset = models.DeliveryProvider.objects.all()
    serializer_class = serializers.DeliveryProvider


class LikesList(APIView):
    """
    Post only, for saving likes

    * Requires token authentication.
    """
    def post(self, request, format=None):
        did_like = request.data.get("did_like")
        try:
            user = request.user
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


class ViewsList(APIView):
    """
    Post only, for saving views

    * Requires token authentication.
    """
    def post(self, request, format=None):
        try:
            user = request.user
            dish = models.Dish.objects.get(pk=request.data.get("dish_id"))
            view = models.View(dish=dish, user=user)
            view.save()
            return Response({"success": True})
        except models.Dish.DoesNotExist:
            return Response({"success": False, "created": False,
                             "Error": "Dish not found"}, 400)


class FulfilmentEventList(APIView):
    """
    Post only, for saving views

    * Requires token authentication.
    """
    def post(self, request, format=None):
        delivery_type = request.data.get("delivery_type")
        booking_type = request.data.get("booking_type")
        try:
            user = request.user
            dish = models.Dish.objects.get(pk=request.data.get("dish_id"))
            if delivery_type is not None:
                delivery = models.DeliveryProvider.objects.get(slug=delivery_type.lower())
                fulfilment = models.FulfilmentEvent(
                    dish=dish, user=user, delivery_provider=delivery)
            if booking_type is not None:
                booking = models.BookingProvider.objects.get(slug=booking_type.lower())
                fulfilment = models.FulfilmentEvent(
                    dish=dish, user=user, booking_provider=booking)
            fulfilment.save()
            return Response({"success": True})
        except models.Dish.DoesNotExist:
            print("Dish not found")
            return Response({"success": False, "created": False,
                             "Error": "Dish not found"}, 400)
        except models.DeliveryProvider.DoesNotExist:
            print("Delivery Provider not found", delivery_type)
            return Response({"success": False, "created": False,
                             "Error": "Delivery Provider not found"}, 400)
        except models.BookingProvider.DoesNotExist:
            print("Booking Provider not found", booking_type)
            return Response({"success": False, "created": False,
                             "Error": "Booking Provider not found"}, 400)


class DonationList(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None):
        """
        Return calculated donated meals from fulfilment events.
        """
        return Response({'count': models.FulfilmentEvent.objects.count()+INIT_DONATIONS})


class SearchTermList(APIView):
    def get(self, request, format=None):
        """
        List all possible search terms
        """
        cuisines = models.Cuisine.objects.all()
        keywords = models.Keyword.objects.all()
        highlights = models.Highlight.objects.all()
        res = {
            "keywords": [keyword.word for keyword in keywords],
            "cuisines": [cuisine.name for cuisine in cuisines],
            'highlights': [highlight.name for highlight in highlights]
        }
        count = len(res['keywords']) + len(res['cuisines']) + len(res['highlights'])
        return Response({'count': count, 'results': res})


class SuburbList(APIView):
    def get(self, request, format=None):
        """
        List all suburbs with restaurants
        """
        rests = models.Restaurant.objects.all().distinct('suburb')
        rests = [rest.suburb for rest in rests]
        return Response({'count': len(rests), 'results': rests})
