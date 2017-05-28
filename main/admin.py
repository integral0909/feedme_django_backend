from django.contrib import admin
from django import forms
from main.models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


# Forms

class DishAdminForm(forms.ModelForm):
    class Meta:
        fields = '__all__'
        model = Dish
        widgets = {
            'keywords': forms.CheckboxSelectMultiple
        }


# Inlines

class OpeningTimeInline(admin.TabularInline):
    model = OpeningTime


class DishInline(admin.TabularInline):
    model = Dish
    fields = ('title', 'price', 'instagram_user', 'keywords', 'image_url')


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )
    list_display = ('__str__', 'is_staff',
                    'get_provider', 'get_likes')
    list_select_related = ('profile', )
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'profile__provider')

    def get_likes(self, inst):
        return inst.likes.count()
    get_likes.short_description = 'Likes'

    def get_provider(self, inst):
        return inst.profile.provider
    get_provider.short_description = 'Provider'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

class TagInline(admin.TabularInline):
    model = Tag
    fields = ('name', )


# Admin models

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('__str__', )

@admin.register(DishQuery)
class DishQueryAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'result_size', 'page', 'radius_km', 'price_range',
                    'has_delivery', 'has_booking', 'suburb')
    list_filter = ('has_delivery', 'has_booking')
    readonly_fields = ('latitude', 'longitude',  'result_size', 'page', 'price_range',
                       'min_price', 'max_price', 'has_delivery', 'has_booking', 'suburb',
                       'keywords', 'cuisines', 'highlights', 'radius_km')
    fields = (('latitude', 'longitude', 'radius_km'),  ('result_size', 'page'),
              'price_range', ('has_delivery', 'has_booking'), 'suburb',
              ('keywords', 'cuisines', 'highlights'), 'user', 'from_location')
    search_fields = ('user', 'suburb')

    def price_range(self, ins):
        try:
            return '${:,.2} -- ${:,.2}'.format(ins.min_price/100, ins.max_price/100)
        except TypeError:
            return 'N/A'

    def radius_km(self, ins):
        try:
            return '{:,}km'.format(ins.max_distance_meters//1000)
        except TypeError:
            return 'N/A'
    radius_km.short_description = 'Distance'


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
    form = DishAdminForm
    list_display = ('__str__', 'restaurant', 'price_format', 'keyword_list_html',
                    'tag_list_html')
    list_filter = ('keywords', )
    # inlines = [TagInline, ]
    search_fields = ('title', 'tags')


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
    search_fields = ('user__username', 'firebase_id', 'fb_id')
    list_filter = ('provider', 'country', 'state', 'city')
    list_display = ('__str__', 'user')


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

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Highlight, SlugNameAdmin)
admin.site.register(Cuisine, SlugNameAdmin)
admin.site.register(Keyword, SlugNameAdmin)
admin.site.register(Blog)
admin.site.register(OpeningTime)
admin.site.register(LikeTransaction, LikeAdmin)
