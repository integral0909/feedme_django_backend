from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^dish/(?P<dish_id>[0-9]+)/$', views.deeplink_dish),
]
