from django import forms
from django.conf import settings
from better_filter_widget import BetterFilterWidget
from timezone_field import TimeZoneFormField
from s3direct.widgets import S3DirectWidget
from main.models import (Cuisine, Highlight, DeliveryProvider, Restaurant, Blog, Dish,
                         Recipe, RecipeIngredient, Cuisine, Highlight, Tag, OpeningTime,
                         Ingredient)
import uuid


def _get_cdn_image(data):
    return '%s%s' % (settings.CDN_URL, data.get('image_url', '').split('/')[-1:][0])


class RestaurantForm(forms.ModelForm):
    name = forms.CharField(label='Restaurant name', max_length=100, required=True,
                           min_length=2)
    image_url = forms.URLField(label='Image', widget=S3DirectWidget(dest='raw-img'))
    address = forms.CharField(max_length=255, min_length=10, required=True)
    cuisines = forms.ModelMultipleChoiceField(widget=BetterFilterWidget,
                                              queryset=Cuisine.objects.all())
    information = forms.CharField(label='Description', widget=forms.Textarea,
                                  min_length=10)
    highlights = forms.ModelMultipleChoiceField(queryset=Highlight.objects.all(),
                                                widget=BetterFilterWidget)
    phone_number = forms.CharField(required=True)
    suburb = forms.CharField(max_length=100, min_length=2, required=True,
                             help_text='Auto-filled by address')
    timezone = TimeZoneFormField(help_text='Auto-filled by address')
    instagram_user = forms.CharField(label='Photo credit', max_length=61, min_length=2,
                                     required=False)
    quandoo_id = forms.IntegerField(label='Quandoo ID', min_value=1, required=False)
    delivery_provider = forms.ModelChoiceField(label='Delivery service provider',
                                               queryset=DeliveryProvider.objects.all(),
                                               required=False)
    delivery_link = forms.URLField(required=False)

    class Meta:
        model = Restaurant
        fields = ('name', 'image_url', 'address', 'cuisines', 'information', 'highlights',
                  'phone_number', 'suburb', 'instagram_user', 'quandoo_id',
                  'delivery_provider', 'delivery_link', 'latitude', 'longitude',
                  'time_offset_minutes', 'firebase_id', 'id', 'timezone')
        widgets = {
            'highlights': BetterFilterWidget(),
            'cuisines': BetterFilterWidget(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'time_offset_minutes': forms.HiddenInput(),
            'id': forms.HiddenInput()
        }

    def save(self, commit=True):
        data = self.cleaned_data
        obj = super(RestaurantForm, self).save(commit=False)
        obj.image_url = _get_cdn_image(data)
        obj.location = 'POINT({0} {1})'.format(data.get('longitude'),
                                               data.get('latitude'))
        obj.firebase_id = uuid.uuid4().hex
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class BlogForm(forms.ModelForm):
    image_url = forms.URLField(label='Image', widget=S3DirectWidget(dest='raw-img'))
    restaurant_id = forms.IntegerField(min_value=0, widget=forms.HiddenInput(),
                                       required=False)

    class Meta:
        model = Blog
        fields = ('author', 'image_url', 'title', 'url', 'restaurant_id', 'id')

    def save(self, commit=True):
        obj = super(BlogForm, self).save(commit=False)
        obj.image_url = _get_cdn_image(self.cleaned_data)
        obj.firebase_id = uuid.uuid4().hex
        if commit:
            obj.save()
            self.save_m2m()
        try:
            restaurant = Restaurant.objects.get(pk=self.cleaned_data.get('restaurant_id'))
        except Restaurant.DoesNotExist:
            pass
        else:
            restaurant.blogs.add(obj)
        return obj


class DishForm(forms.ModelForm):
    image_url = forms.URLField(label='Image', widget=S3DirectWidget(dest='raw-img'))

    class Meta:
        model = Dish
        fields = ('image_url', 'price', 'title', 'description', 'instagram_user',
                  'keywords', 'tags', 'restaurant')
        widgets = {
            'keywords': forms.CheckboxSelectMultiple(),
            'tags': BetterFilterWidget(),
            'restaurant': forms.HiddenInput()
        }
        labels = {
            'title': 'Name',
            'instagram_user': 'Photo credit',
            'price': 'Price in cents',
            'keywords': 'Dietary tags',
        }
        help_texts = {
            'tags': '''Add ingredients this dish has. If you need to create a new tag,
                    please spell check it first.''',
            'price': '''Numbers only. Multiply dollars by 100.
                     For example for $14.95 input 1495 or for $10 input 1000.'''
        }

    def save(self, commit=True):
        obj = super(DishForm, self).save(commit=False)
        obj.image_url = _get_cdn_image(self.cleaned_data)
        obj.firebase_id = uuid.uuid4().hex
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class RecipeForm(forms.ModelForm):
    image_url = forms.URLField(label='Image', widget=S3DirectWidget(dest='raw-img'))
    dish = forms.ModelChoiceField(queryset=Dish.objects.none(), label='For Dish',
                                  widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        try:
            qs = kwargs.pop('dish_opts')
        except KeyError:
            pass
        super(RecipeForm, self).__init__(*args, **kwargs)
        try:
            self.fields['dish'].queryset = qs
        except UnboundLocalError:
            pass

    def save(self, commit=True):
        recipe = super(RecipeForm, self).save(commit=commit)
        if self.cleaned_data.get('dish'):
            dish.recipe = recipe
            dish.save()
        return recipe

    class Meta:
        model = Recipe
        fields = '__all__'
        exclude = ('steps', 'total_time_seconds', 'likes_count', 'views_count')
        widgets = {
            'keywords': forms.CheckboxSelectMultiple(),
            'tags': BetterFilterWidget(),
        }


class RecipeIngredientForm(forms.ModelForm):
    class Meta:
        model = RecipeIngredient
        fields = '__all__'
        widgets = {
            'recipe': forms.HiddenInput()
        }
        exclude = ('valid_from', 'valid_through')

    def save(self, commit=True):
        obj = super(RecipeIngredientForm, self).save(commit=False)
        obj.preparation = obj.preparation.lower()
        obj.unit_type = obj.unit_type.lower()
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class CuisineForm(forms.ModelForm):
    class Meta:
        model = Cuisine
        fields = ['name']


class HighlightForm(forms.ModelForm):
    class Meta:
        model = Highlight
        fields = ['name']


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'description']

    def save(self, commit=True):
        obj = super(IngredientForm, self).save(commit=False)
        obj.name = obj.name.title()
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class RestaurantOpeningTimeForm(forms.ModelForm):
    class Meta:
        model = OpeningTime
        fields = '__all__'
        widgets = {
            'restaurant': forms.HiddenInput()
        }
        labels = {
            'day_of_week': 'Day of the week'
        }
