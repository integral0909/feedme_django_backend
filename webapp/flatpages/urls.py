from webapp.flatpages import views
from django.conf.urls import url, include
from django.views.generic import RedirectView


urlpatterns = [
    url(r'^(?P<page>[\w]+)/$', views.load_flatpage, name='about'),
    url(r'^impact\.html$', RedirectView.as_view(url='/about/', permanent=True)),
    url(r'^impact/$', RedirectView.as_view(url='/about/', permanent=True)),
    url(r'^terms/$', views.load_flatpage, name='terms'),
    url(r'^terms\.html$', RedirectView.as_view(url='/terms/', permanent=True)),
    url(r'^privacy/$', views.load_flatpage, name='privacy'),
    url(r'^privacy\.html$', RedirectView.as_view(url='/privacy/', permanent=True)),
    url(r'^donation/$', views.load_flatpage, name='donation'),
    url(r'^donation\.html$', RedirectView.as_view(url='/donation/', permanent=True)),
    url(r'^events/$', views.load_flatpage, name='events'),
    url(r'^events\.html$', RedirectView.as_view(url='/events/', permanent=True)),
    url(r'^team/$', views.load_flatpage, name='team'),
    url(r'^team\.html$', RedirectView.as_view(url='/team/', permanent=True)),
    url(r'^index\.html$', RedirectView.as_view(url='/home/', permanent=True)),
    url(r'^$', views.load_flatpage, name='home'),
]
