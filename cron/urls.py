from django.conf.urls import url
from django.contrib import admin
from . import views


urlpatterns = [
    url(r'^db/backup/', views.backup_db),
    url(r'^randomise/dishes/', views.randomise_dishes),
]
