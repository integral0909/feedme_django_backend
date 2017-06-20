from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^restaurants/add/', views.change_restaurant),
    url(r'^restaurants/(?P<rest_id>[0-9]+)/change/(?P<tab>[\w]+)/', views.change_restaurant),
    url(r'^restaurants/(?P<rest_id>[0-9]+)/change/', views.change_restaurant),
    url(r'^(?P<list_type>[\w]+)/', views.list_items),
]
