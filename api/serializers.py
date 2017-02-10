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
        fields = ('author', 'image_url', 'title', 'url')


class Profile(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='profile-detail')
    user = User()

    class Meta:
        model = models.Profile
        fields = ('user', 'photo_url', 'fb_id', 'provider', 'bio', 'country', 'state',
                  'city', 'created', 'updated')


class Highlight(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='highlight-detail')

    class Meta:
        model = models.Highlight
        fields = '__all__'


class Cuisine(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='cuisine-detail')

    class Meta:
        model = models.Cuisine
        fields = '__all__'


class OpeningTime(serializers.ModelSerializer):
    class Meta:
        model = models.OpeningTime
        fields = ('opens', 'closes', 'day_of_week', 'valid_from', 'valid_through')


class Keyword(serializers.ModelSerializer):
    class Meta:
        model = models.Keyword
        fields = ('word', )


class Restaurant(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='restaurant-detail')
    cuisines = Cuisine(many=True)
    hightlights = Highlight(many=True)
    opening_times = OpeningTime(many=True)
    blogs = Blog(many=True)

    class Meta:
        model = models.Restaurant
        fields = ('url', 'name', 'image_url', 'address', 'cuisines', 'information',
                  'hightlights', 'blogs', 'phone_number', 'suburb', 'instagram_user',
                  'time_offset_minutes', 'tripadvisor_widget', 'location',
                  'opening_times')


class Dish(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dish-detail')
    restaurant = Restaurant(read_only=True)
    keywords = Keyword(many=True)

    class Meta:
        model = models.Dish
        fields = ('url', 'restaurant', 'image_url', 'price', 'title', 'instagram_user',
                  'keywords')
