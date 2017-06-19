from django import forms
from better_filter_widget import BetterFilterWidget
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from main.models import Cuisine, Highlight, DeliveryProvider


class RestaurantForm(forms.Form):
    name = forms.CharField(label='Restaurant name', max_length=100, required=True,
                           min_length=2)
    image = forms.ImageField(label='Restaurant image', required=True)
    address = forms.CharField(max_length=255, min_length=10, required=True)
    cuisines = forms.ModelMultipleChoiceField(widget=BetterFilterWidget,
                                              queryset=Cuisine.objects.all())
    information = forms.CharField(label='Description', widget=forms.Textarea,
                                  min_length=10)
    highlights = forms.ModelMultipleChoiceField(queryset=Highlight.objects.all(),
                                                widget=BetterFilterWidget)
    phone_number = PhoneNumberField(required=True, widget=PhoneNumberPrefixWidget)
    suburb = forms.CharField(max_length=100, min_length=2, required=True)
    instagram_user = forms.CharField(label='Photo credit', max_length=61, min_length=2,
                                     required=True)
    # Some sort of timezone offset selector?
    # Location should be set via address and Google Places API or 3rd party.
    quandoo_id = forms.IntegerField(label='Quandoo ID', min_value=1, required=False)
    delivery_provider = forms.ModelChoiceField(label='Delivery service provider',
                                               queryset=DeliveryProvider.objects.all())
    delivery_link = forms.URLField()

    class Meta:
        widgets = {
            'highlights': BetterFilterWidget(),
            'cuisines': BetterFilterWidget(),
        }
