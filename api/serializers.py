from django.contrib.auth.models import User, Group
import main.models as models
from rest_framework import serializers


class User(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="user-detail")

    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class Group(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class Blog(serializers.ModelSerializer):
    class Meta:
        model = models.Blog
        fields = ('author', 'image_url', 'title', 'url', 'firebase_id')


class Profile(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='profile-detail')
    user = User()

    class Meta:
        model = models.Profile
        fields = ('user', 'photo_url', 'fb_id', 'provider', 'bio', 'country', 'state',
                  'city', 'created', 'updated')


class Highlight(serializers.ModelSerializer):
    def to_representation(self, obj):
        return obj.name

    class Meta:
        model = models.Highlight
        fields = ('name', 'slug')


class Cuisine(serializers.ModelSerializer):
    def to_representation(self, obj):
        return obj.name

    class Meta:
        model = models.Cuisine
        fields = ('name', 'slug')


class OpeningTime(serializers.ModelSerializer):
    class Meta:
        model = models.OpeningTime
        fields = ('opens', 'closes', 'day_of_week', 'valid_from', 'valid_through')


class Keyword(serializers.ModelSerializer):
    def to_representation(self, obj):
        return obj.word

    class Meta:
        model = models.Keyword
        fields = ('word', )


class DeliveryProvider(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='deliveryprovider-detail')

    class Meta:
        model = models.DeliveryProvider
        fields = ('url', 'name', 'slug', 'title', 'description', 'logo_url')


class Restaurant(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='restaurant-detail')
    cuisines = Cuisine(many=True)
    highlights = Highlight(many=True)
    opening_times = OpeningTime(many=True)
    blogs = Blog(many=True)
    delivery_provider = DeliveryProvider()

    class Meta:
        model = models.Restaurant
        fields = ('url', 'name', 'image_url', 'address', 'cuisines', 'information',
                  'highlights', 'blogs', 'phone_number', 'suburb', 'instagram_user',
                  'time_offset_minutes', 'tripadvisor_widget', 'location',
                  'opening_times', 'delivery_provider', 'delivery_link',
                  'firebase_id')


class Dish(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dish-detail')
    restaurant = Restaurant(read_only=True)
    keywords = Keyword(many=True)

    class Meta:
        model = models.Dish
        fields = ('url', 'restaurant', 'image_url', 'price', 'title',
                  'instagram_user', 'keywords', 'firebase_id')
