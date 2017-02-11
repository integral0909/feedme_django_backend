from django.contrib import admin
from main.models import *

# Register your models here.


class OpeningTimeInline(admin.TabularInline):
    model = OpeningTime


class DishInline(admin.TabularInline):
    model = Dish
    fields = ('title', 'price', 'instagram_user', 'keywords', 'image_url')


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    inlines = [OpeningTimeInline, DishInline]


class SlugNameAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'slug')


class DishAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'restaurant', 'price_format', 'keyword_list_html')


admin.site.register(Highlight, SlugNameAdmin)
admin.site.register(Cuisine, SlugNameAdmin)
admin.site.register(Keyword, SlugNameAdmin)
admin.site.register(Blog)
admin.site.register(Dish, DishAdmin)
admin.site.register(OpeningTime)
