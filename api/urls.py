from django.conf.urls import url, include
from rest_framework import routers
from . import views
from api import reporting

router = routers.DefaultRouter()
router.register(r'restaurants', views.RestaurantViewSet)
router.register(r'dishes', views.DishViewSet)
router.register(r'recipes', views.RecipeViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^geocode/', views.Geocode.as_view()),
    url(r'^reporting/', include('api.reporting.urls')),
    url(r'^likes/(?P<subject>[\w]+)/', views.LikesList.as_view()),
    url(r'^likes/', views.LikesList.as_view()),
    url(r'^restaurants/(?P<restaurant_pk>.+)/dishes/$',
        views.RestaurantDishesViewSet.as_view()),
    url(r'^views/(?P<subject>[\w]+)/', views.ViewsList.as_view()),
    url(r'^views/', views.ViewsList.as_view()),
    url(r'^fulfilment-events/', views.FulfilmentEventList.as_view()),
    url(r'^recipe-requests/', views.RecipeRequestList.as_view()),
    url(r'^donations/', views.DonationList.as_view()),
    url(r'^dishes/(?P<dish_pk>.+)/recipe/$', views.DishRecipesViewSet.as_view()),
    url(r'^search-terms/', views.SearchTermList.as_view()),
    url(r'^suburbs/', views.SuburbList.as_view()),
    url(r'^ingest/recipe/', views.RecipeIngest.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
