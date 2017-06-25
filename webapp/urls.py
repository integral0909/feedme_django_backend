from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^restaurants/((?P<restaurant_slug>[\w\-]+))/', views.restaurant_detail,
        name='restaurant-detail'),
    url(r'^dishes/(?P<dish_id>[0-9]+)/$', views.dish_detail),
    url(r'^dish/(?P<dish_id>[0-9]+)/$', views.dish_detail),
    # url(r'^saved-items/'),
    # url(r'^feed/', )
]
