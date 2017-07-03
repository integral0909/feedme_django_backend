from django.contrib.flatpages import views
from django.conf.urls import url, include
from django.views.generic import RedirectView


urlpatterns = [
    url(r'^about/$', views.flatpage, {'url': '/about/'}, name='about'),
    url(r'^impact\.html$', RedirectView.as_view(url='/about/', permanent=True)),
    url(r'^impact/$', RedirectView.as_view(url='/about/', permanent=True)),
    url(r'^terms/$', views.flatpage, {'url': '/terms/'}, name='terms'),
    url(r'^terms\.html$', RedirectView.as_view(url='/terms/', permanent=True)),
    url(r'^privacy/$', views.flatpage, {'url': '/privacy/'}, name='privacy'),
    url(r'^privacy\.html$', RedirectView.as_view(url='/privacy/', permanent=True)),
    url(r'^donation/$', views.flatpage, {'url': '/donation/'}, name='donation'),
    url(r'^donation\.html$', RedirectView.as_view(url='/donation/', permanent=True)),
    url(r'^events/$', views.flatpage, {'url': '/events/'}, name='events'),
    url(r'^events\.html$', RedirectView.as_view(url='/events/', permanent=True)),
    url(r'^team/$', views.flatpage, {'url': '/team/'}, name='team'),
    url(r'^team\.html$', RedirectView.as_view(url='/team/', permanent=True)),
    url(r'^home/$', RedirectView.as_view(url='/home/', permanent=True)),
    url(r'^$', views.flatpage, {'url': '/home/'}, name='home'),
]
