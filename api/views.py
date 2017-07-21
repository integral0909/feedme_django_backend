from datetime import datetime, timedelta, timezone
from django.contrib.auth.models import User, Group
from django.db.models import Count, Sum
from rest_framework import viewsets, generics, pagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.conf import settings
from django.db import IntegrityError
import api.serializers as serializers
import main.models as models
from data_entry.models import RecipeDraft, IngredientDraft
import api.filters as filters
from django_sqs_jobs import queues
from data_entry.jobs import PrepopulateImage

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
            if self.request.query_params.get('count') == 'true':
                return Response({
                    'count': models.Dish.objects.saved(self.request.user).count()
                })
            queryset = models.Dish.objects.saved(self.request.user)\
                             .order_by_distance(
                location=request.query_params.get('from_location', '').split(',')
            )
        else:
            queryset = self.filter_queryset(self.get_queryset().reduce_by_distance(
                location=request.query_params.get('from_location', '').split(','),
                meters=request.query_params.get('max_distance_meters', '')
            ).not_liked(self.request.user).fresh(self.request.user)
             .order_by('random', 'id').distinct('random', 'id'))

            models.DishQuery().log(request=request, results=queryset.count())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(convertedSet, many=True)
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all()
    serializer_class = serializers.Recipe
    filter_class = filters.Recipe

    def list(self, request, *args, **kwargs):
        if self.request.query_params.get('saved') == 'true':
            if self.request.query_params.get('count') == 'true':
                return Response({
                    'count': models.Recipe.objects.saved(self.request.user).count()
                })
            queryset = models.Recipe.objects.saved(self.request.user)
        else:
            queryset = self.filter_queryset(
                self.get_queryset().not_liked(self.request.user).fresh(self.request.user)
                    .order_by('random', 'id').distinct('random', 'id')
            )

            models.RecipeQuery().log(request=request, results=queryset.count())

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


class DishRecipesViewSet(APIView):
    """Recipe for a particular dish."""
    def get(self, request, format=None, dish_pk=None):
        try:
            dish = models.Dish.objects.get(pk=dish_pk)
        except models.Dish.DoesNotExist:
            print('DishRecipe: Dish does not exist')
            return Response({'Error': 'Dish not found'}, 400)
        else:
            serializer = serializers.Recipe(dish.recipe)
            return Response({'recipe': serializer.data})


class DeliveryProviderViewSet(viewsets.ModelViewSet):
    queryset = models.DeliveryProvider.objects.all()
    serializer_class = serializers.DeliveryProvider


class LikesList(APIView):
    """Post only, for saving likes."""
    def post(self, request, format=None, subject='dishes'):
        did_like = request.data.get("did_like")
        user = request.user
        subject_class, class_name, like_class, view_class = self._setup_type(subject)
        try:
            obj = subject_class.objects.get(pk=request.data.get("{}_id".format(class_name)))
        except subject_class.DoesNotExist:
            return self._error_response(class_name)
        try:
            like = like_class.objects.get(**{class_name: obj, 'user': user})
            like.did_like = did_like
            like.save()
            return Response({"success": True, "created": False})
        except like_class.DoesNotExist:
            like = like_class(**{'user': user, class_name: obj, 'did_like': did_like})
            like.save()
            return Response({"success": True, "created": True})

    @staticmethod
    def _setup_type(subject):
        if subject == 'recipes':
            subject_class = models.Recipe
            class_name = 'recipe'
            like_class = models.RecipeLike
            view_class = models.RecipeView
        else:
            subject_class = models.Dish
            class_name = 'dish'
            like_class = models.Like
            view_class = models.View
        return subject_class, class_name, like_class, view_class

    @staticmethod
    def _error_response(class_name):
        return Response({"success": False, "created": False,
                         "Error": "{} not found".format(class_name.upper())}, 400)


class ViewsList(LikesList):
    """Post only, for saving views."""
    def post(self, request, format=None, subject='dishes'):
        user = request.user
        subject_class, class_name, like_class, view_class = self._setup_type(subject)
        try:
            obj = subject_class.objects.get(pk=request.data.get("{}_id".format(class_name)))
        except subject_class.DoesNotExist:
            return self._error_response(class_name)
        view = view_class(**{class_name: obj, 'user': user})
        view.save()
        return Response({"success": True})


class RecipeIngest(APIView):
    """Receives draft recipes as JSON."""
    authentication_classes = [ScraperAuthentication]
    queue = queues.SQSQueue()

    def post(self, request):
        """Must update raw properties and check for checksum changes."""
        data = request.data
        source_url = data.get('source_url')
        kwargs = {'name_raw': data.get('name'), 'description_raw': data.get('description', ''),
            'servings_raw': data.get('serves', ''), 'prep_time_raw': data.get('prep_time', ''),
            'cook_time_raw': data.get('cook_time', ''), 'difficulty_raw': data.get('difficulty', ''),
            'image_url_raw': data.get('image_url', '')}
        try:
            inst = RecipeDraft.objects.get(source_url=source_url)
        except RecipeDraft.DoesNotExist:
            kwargs['source_url'] = source_url
            inst = RecipeDraft(**kwargs)
            inst.prepopulate_with_raw()
            inst.save()
            self.queue.append(PrepopulateImage(inst))
            for val in data.get('ingredients'):
                IngredientDraft.objects.create(raw_text=val, recipe_draft=inst)
        else:
            for key, val in kwargs.items():
                setattr(inst, key, val)
            inst.source_url = source_url
            if inst.checksum_has_changed():
                inst.seen = False
                inst.processed = False
                inst.save()
        return Response({'success': True})





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


class RecipeRequestList(APIView):
    """
    Post only, saves a user's request of a recipe

    * Requires token auth
    """

    def post(self, request, format=None):
        dish_id = request.data.get('dish_id')
        user = request.user
        try:
            dish = models.Dish.objects.get(pk=dish_id)
        except models.Dish.DoesNotExist:
            print("RecipeRequest: Dish not found")
            return Response({'success': False, 'created': False,
                             'error': 'Dish not found'}, 400)
        else:
            models.RecipeRequest.objects.create(dish=dish, user=user)
            return Response({'success': True, 'created': True}, 200)


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
        """List all possible search terms."""
        seen_ing = []
        res = {
            'keywords': [kwd.word for kwd in models.Keyword.objects.all()],
            'highlights': [hlt.name for hlt in models.Highlight.objects.all()],
            'tags': [tag.name for tag in models.Tag.objects.all()],
            'ingredients': [i.name for i in models.Ingredient.objects.all()
                            if not (i.name in seen_ing or seen_ing.append(i.name))]
        }
        count = 0
        for key, val in res.items():
            count += len(val)
        return Response({'count': count, 'results': res})


class SuburbList(APIView):
    def get(self, request, format=None):
        """List all suburbs with restaurants"""
        rests = models.Restaurant.objects.all().distinct('suburb')
        rests = [rest.suburb for rest in rests]
        return Response({'count': len(rests), 'results': rests})


class Geocode(APIView):
    def get(self, request, format=None):
        """Pass parameters via query string and get their transformed value."""
        import googlemaps
        gmaps = googlemaps.Client(key=settings.GOOGLEMAPS_API['key'])
        return_type = request.query_params.get('return')
        if request.query_params.get('address'):
            addr = request.query_params.get('address')
            geocode_results = gmaps.geocode(addr)
            loc = self._extract_coords(geocode_results[0])
            suburb = self._extract_suburb(geocode_results[0])
            return Response({'longitude': loc['lng'], 'latitude': loc['lat'],
                             'suburb': suburb})
        coords = request.query_params.get('coords')
        if coords and return_type == 'timezone':
            georesult = gmaps.timezone(location=coords)
            return Response(georesult)

    @staticmethod
    def _extract_coords(geocode_result):
        return geocode_result['geometry']['location']

    @staticmethod
    def _extract_suburb(geocode_result):
        return (cmp['short_name'] for cmp in geocode_result['address_components']
                if 'locality' in cmp['types'])
