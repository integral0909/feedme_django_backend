from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^modals/(?P<modal>[\w]+)/', views.modal),
    url(r'^(?P<item_type>[\w]+)/(?P<item_id>[0-9]+)/change/(?P<tab>[\w]+)/', views.change_item),
    url(r'^(?P<item_type>[\w]+)/(?P<item_id>[0-9]+)/change/', views.change_item),
    url(r'^(?P<item_type>[\w]+)/add/', views.change_item),
    url(r'^(?P<item_type>[\w]+)/', views.list_items),

]
