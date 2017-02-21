from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^restaurants/((?P<restaurant_slug>[\w\-]+))/', views.restaurant_detail,
        name='restaurant-detail'),
    # url(r'^saved-items/'),
    # url(r'^feed/', )
]
