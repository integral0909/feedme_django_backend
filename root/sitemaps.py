from django.contrib.sitemaps import Sitemap
from main.models import Restaurant, Dish, Recipe
from blog.models import Post


class RestaurantSitemap(Sitemap):
    changefreq = 'monthly'

    def items(self):
        return Restaurant.objects.all()

    def lastmod(self, obj):
        return obj.updated


class DishSitemap(Sitemap):
    changefreq = 'monthly'

    def items(self):
        return Dish.objects.all()

    def lastmod(self, obj):
        return obj.updated


class RecipeSitemap(Sitemap):
    changefreq = 'weekly'

    def items(self):
        return Recipe.objects.all()

    def lastmod(self, obj):
        return obj.updated


class BlogPostSitemap(Sitemap):
    changefreq = 'monthly'

    def items(self):
        return Post.objects.all()

    def lastmod(self, obj):
        return obj.updated


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'

    def items(self):
        return ['impact', 'about', 'terms', 'privacy', 'donation', 'events', 'team']

    def location(self, item):
        return '/{0}/'.format(item)
