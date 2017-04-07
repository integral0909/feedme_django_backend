from django.conf.urls import url, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'restaurants', views.RestaurantViewSet)
router.register(r'dishes', views.DishViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^likes/', views.LikesList.as_view()),
    url(r'^restaurants/(?P<restaurant_pk>.+)/dishes/$',
        views.RestaurantDishesViewSet.as_view()),
    url(r'^views/', views.ViewsList.as_view()),
    url(r'^fulfilment-events/', views.FulfilmentEventList.as_view()),
    url(r'^donations/', views.DonationList.as_view()),
    url(r'^search-terms/', views.SearchTermList.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
