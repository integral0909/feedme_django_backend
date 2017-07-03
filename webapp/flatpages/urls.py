from django.contrib.flatpages import views
from django.conf.urls import url, include
from django.views.generic import RedirectView


urlpatterns = [
    url(r'^about/$', views.flatpage, {'url': '/about/'}, name='about'),
    url(r'^impact\.html$', RedirectView.as_view(url='/about/', permanent=True)),
    url(r'^impact/$', RedirectView.as_view(url='/about/', permanent=True)),
    url(r'^terms/$', views.flatpage, {'url': '/terms/'}, name='terms'),
    url(r'^privacy/$', views.flatpage, {'url': '/privacy/'}, name='privacy'),
    url(r'^donation/$', views.flatpage, {'url': '/donation/'}, name='donation'),
    url(r'^events/$', views.flatpage, {'url': '/events/'}, name='events'),
    url(r'^team/$', views.flatpage, {'url': '/team/'}, name='team'),
    url(r'^home/$', RedirectView.as_view(url='/home/', permanent=True)),
    url(r'^$', views.flatpage, {'url': '/home/'}, name='home'),
]
