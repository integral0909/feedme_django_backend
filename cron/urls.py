from django.conf.urls import url
from django.contrib import admin
from . import views


urlpatterns = [
    url(r'^db/backup/', views.backup_db),
    url(r'^randomise/dishes/', views.randomise_dishes),
    url(r'^randomise/recipes/', views.randomise_recipes),
    url(r'^validate/dishes/', views.validate_dish_integrity),
    url(r'^validate/recipes/', views.validate_recipe_integrity),
    url(r'^process/draft/recipes/', views.process_draft_recipes),
]
