"""root URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf import settings
# from django.contrib import admin
from ratelimitbackend import admin
from django_sqs_jobs.views import JobMessageView
from django.contrib.sitemaps.views import sitemap
from sitemaps.maps import (RecipeSitemap, RestaurantSitemap, DishSitemap, StaticViewSitemap,
                           BlogPostSitemap, RecipeCollectionSitemap)
# from ratelimitbackend import views as auth_views

admin.autodiscover()
# Text to put in each page's <title>.
admin.site.site_title = '%s | Admin' % settings.PROJECT_TITLE
# Text to put in each page's <h1> (and above login form).
admin.site.site_header = '%s Admin' % settings.PROJECT_TITLE_ABBR
# Text to put at the top of the admin index page.
# admin.site.index_title = settings.

sitemaps = {
    'dishes': DishSitemap,
    'recipes': RecipeSitemap,
    'collections': RecipeCollectionSitemap,
    'restaurants': RestaurantSitemap,
    'static': StaticViewSitemap,
    'blogs': BlogPostSitemap
}

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('api.urls')),
    url(r'^cron/', include('cron.urls')),
    url(r'^jobs/$', JobMessageView.as_view()),
    url(r'^hijack/', include('hijack.urls')),
    url(r'^data-entry/', include('data_entry.urls')),
    url(r'^s3direct/', include('s3direct.urls')),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),
    url(r'^explorer/', include('explorer.urls')),
    url(r'^', include('main.urls'))
]
