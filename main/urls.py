from django.conf.urls import url, include
from django.contrib import admin
from . import views
from django.contrib.auth import views as auth_views
from ratelimitbackend.views import login as r_login
import blog.views

urlpatterns = [
    # url(r'^$', r_login, name='index'),
    url(r'^reporting/', views.report),
    url(r'^', include('webapp.urls')),
    url(r'^home/', views.home, name='home'),
    url(r'^accounts/', include('auth.urls')),
]
