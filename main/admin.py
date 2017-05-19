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
    list_display = ('__str__', 'address', 'quandoo_id', 'delivery_provider',
                    'delivery_link', 'cuisine_list_html', )
    readonly_fields = ('latitude', 'longitude', 'firebase_id')
    list_editable = ('quandoo_id', 'delivery_provider', 'delivery_link')
    list_filter = ('delivery_provider', 'cuisines', 'highlights')
    search_fields = ('name', 'dishes__title')


class SlugNameAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'slug')
    readonly_fields = ('slug', )


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'restaurant', 'price_format', 'keyword_list_html')
    list_filter = ('keywords', )
    search_fields = ('title', )


@admin.register(DeliveryProvider)
class DeliveryProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'title', 'logo_url', 'description')
    list_editable = ('title', 'logo_url', 'description')
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BookingProvider)
class BookingProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'title', 'logo_url', 'description')
    list_editable = ('title', 'logo_url', 'description')
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('dish', 'user', 'did_like', 'created', 'updated')
    search_fields = ('dish__name', 'user__profile__first_name',
                     'user__profile__last_name')


@admin.register(View)
class ViewAdmin(admin.ModelAdmin):
    list_display = ('dish', 'user', 'created')
    search_fields = ('dish__name', 'user__profile__first_name',
                     'user__profile__last_name')


@admin.register(FulfilmentEvent)
class FulfilmentEventAdmin(admin.ModelAdmin):
    list_display = ('dish', 'delivery_provider', 'booking_provider', 'user', 'created')
    list_filter = ('delivery_provider', 'booking_provider', 'dish')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username',)


class RecipeStepInline(admin.TabularInline):
    model = RecipeStep


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeStepInline, RecipeIngredientInline)
    list_display = ('__str__', 'description', 'ingredient_text', 'created')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'description')


admin.site.register(Highlight, SlugNameAdmin)
admin.site.register(Cuisine, SlugNameAdmin)
admin.site.register(Keyword, SlugNameAdmin)
admin.site.register(Blog)
admin.site.register(OpeningTime)
