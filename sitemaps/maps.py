from django.contrib.sites.models import Site
from sitemaps import SubdomainSite, SubdomainSitemap
from main.models import Restaurant, Dish, Recipe, RecipeCollection
from blog.models import Post

current_site = Site.objects.get_current()


class RestaurantSitemap(SubdomainSitemap):
    changefreq = 'monthly'
    subdomain = SubdomainSite('use', current_site)
    protocol = 'https'

    def items(self):
        return Restaurant.objects.all()

    def lastmod(self, obj):
        return obj.updated


class DishSitemap(SubdomainSitemap):
    changefreq = 'monthly'
    subdomain = SubdomainSite('use', current_site)
    protocol = 'https'

    def items(self):
        return Dish.objects.all()

    def lastmod(self, obj):
        return obj.updated


class RecipeSitemap(SubdomainSitemap):
    changefreq = 'weekly'
    subdomain = SubdomainSite('www', current_site)
    protocol = 'https'

    def items(self):
        return Recipe.objects.all()

    def lastmod(self, obj):
        return obj.updated


class RecipeCollectionSitemap(SubdomainSitemap):
    changefreq = 'monthly'
    subdomain = SubdomainSite('www', current_site)
    protocol = 'https'

    def items(self):
        return RecipeCollection.objects.all()


class BlogPostSitemap(SubdomainSitemap):
    changefreq = 'monthly'
    subdomain = SubdomainSite('www', current_site)
    protocol = 'https'

    def items(self):
        return Post.objects.all()

    def lastmod(self, obj):
        return obj.updated

    def location(self, obj):
        return obj.get_absolute_url()


class StaticViewSitemap(SubdomainSitemap):
    changefreq = 'weekly'
    subdomain = SubdomainSite('www', current_site)
    protocol = 'https'

    def items(self):
        return ['impact', 'about', 'terms', 'privacy', 'donation', 'events', 'team']

    def location(self, item):
        return '/{0}/'.format(item)
