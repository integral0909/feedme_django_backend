from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^reporting/', views.report),
    url(r'^', include('webapp.urls')),
    url(r'^home/', views.home, name='home'),
    url(r'^accounts/', include('auth.urls')),
]
