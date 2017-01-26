from django.conf.urls import url, include
from django.contrib import admin
from . import views
from django.contrib.auth import views as auth_views
from ratelimitbackend.views import login as r_login

urlpatterns = [
    url(r'^$', r_login, name='index'),
    url(r'^home/', views.home, name='home'),
    url('^accounts/', include('auth.urls')),
]
