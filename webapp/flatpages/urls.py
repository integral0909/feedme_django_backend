from django.contrib.flatpages import views
from django.conf.urls import url, include


urlpatterns = [
    url(r'^about/$', views.flatpage, {'url': '/about/'}, name='about'),
    url(r'^impact\.html$', views.flatpage, {'url': '/about/'}, name='about'),
    url(r'^impact/$', views.flatpage, {'url': '/about/'}, name='about'),
    url(r'^license/$', views.flatpage, {'url': '/license/'}, name='license'),
]
