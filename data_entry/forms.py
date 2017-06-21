from django import forms
from better_filter_widget import BetterFilterWidget
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from timezone_field import TimeZoneFormField
from s3direct.widgets import S3DirectWidget
from main.models import (Cuisine, Highlight, DeliveryProvider, Restaurant, Blog, Dish,
                         Recipe)
import pytz


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
    # Some sort of timezone offset selector?
    # Location should be set via address and Google Places API or 3rd party.
    quandoo_id = forms.IntegerField(label='Quandoo ID', min_value=1, required=False)
    delivery_provider = forms.ModelChoiceField(label='Delivery service provider',
                                               queryset=DeliveryProvider.objects.all())
    delivery_link = forms.URLField()

    class Meta:
        model = Restaurant
        fields = ('name', 'image_url', 'address', 'cuisines', 'information', 'highlights',
                  'phone_number', 'suburb', 'instagram_user', 'quandoo_id',
                  'delivery_provider', 'delivery_link', 'latitude', 'longitude')
        widgets = {
            'highlights': BetterFilterWidget(),
            'cuisines': BetterFilterWidget(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput()
        }


class BlogForm(forms.ModelForm):
    image_url = forms.URLField(label='Image', widget=S3DirectWidget(dest='raw-img'))
    restaurant_id = forms.IntegerField(min_value=0, widget=forms.HiddenInput())

    class Meta:
        model = Blog
        fields = ('author', 'image_url', 'title', 'url', 'restaurant_id')

    def save(self, commit=True):
        restaurant = Restaurant.objects.get(pk=self.cleaned_data['restaurant_id'])
        obj = super(BlogForm, self).save(commit=commit)
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


class RecipeForm(forms.ModelForm):
    image_url = forms.URLField(label='Image', widget=S3DirectWidget(dest='raw-img'))

    class Meta:
        model = Recipe
        fields = '__all__'
        exclude = ('steps', 'total_time_seconds', 'likes_count', 'views_count')
        widgets = {
            'keywords': forms.CheckboxSelectMultiple(),
            'tags': BetterFilterWidget(),
        }
