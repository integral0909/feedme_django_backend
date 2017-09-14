from webapp.flatpages import views
from django.conf.urls import url, include
from django.views.generic import RedirectView


urlpatterns = [
    url(r'^terms/', views.FlatView.as_view(template_name='terms.html')),
    url(r'^privacy/', views.FlatView.as_view(template_name='privacy.html')),
    url(r'^impact\.html$', RedirectView.as_view(url='/impact/', permanent=True)),
    url(r'^terms\.html$', RedirectView.as_view(url='/terms/', permanent=True)),
    url(r'^privacy\.html$', RedirectView.as_view(url='/privacy/', permanent=True)),
    url(r'^privacy-policy/$', RedirectView.as_view(url='/privacy/', permanent=True)),
    url(r'^donation\.html$', RedirectView.as_view(url='/donation/', permanent=True)),
    url(r'^events\.html$', RedirectView.as_view(url='/events/', permanent=True)),
    url(r'^team\.html$', RedirectView.as_view(url='/team/', permanent=True)),
    url(r'^index\.html$', RedirectView.as_view(url='/home/', permanent=True)),
]
