from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^((?P<slug>[\w\-]+))/', views.display_post, name='blog-post'),
    url(r'^', views.list_posts),
]
