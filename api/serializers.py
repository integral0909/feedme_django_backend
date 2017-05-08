from django.contrib.auth.models import User
import main.models as models
from rest_framework import serializers
from api.fields import NullCharField


class User(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="user-detail")

    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


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


class DeliveryProvider(serializers.ModelSerializer):
    # url = serializers.HyperlinkedIdentityField(view_name='deliveryprovider-detail')

    class Meta:
        model = models.DeliveryProvider
        fields = ('name', 'slug', 'title', 'description', 'logo_url')


class DishLight(serializers.ModelSerializer):
    pg_id = serializers.SerializerMethodField('get_namespaced_id')
    keywords = Keyword(many=True)

    def get_namespaced_id(self, obj):
        return obj.id

    class Meta:
        model = models.Dish
        fields = ('pg_id', 'image_url', 'price', 'title', 'instagram_user',
                  'keywords', 'firebase_id')


class Restaurant(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='restaurant-detail')
    pg_id = serializers.SerializerMethodField('get_namespaced_id')
    cuisines = Cuisine(many=True)
    highlights = Highlight(many=True)
    # opening_times = OpeningTime(many=True)
    blogs = Blog(many=True)
    # delivery_provider = DeliveryProvider()
    delivery_type = serializers.SerializerMethodField()
    delivery_link = NullCharField()

    def get_namespaced_id(self, obj):
        return obj.id

    def get_delivery_type(self, obj):
        if obj.delivery_provider is not None:
            return obj.delivery_provider.slug
        return None

    class Meta:
        model = models.Restaurant
        fields = ('url', 'pg_id', 'name', 'image_url', 'address', 'cuisines',
                  'information', 'highlights', 'blogs', 'phone_number', 'suburb',
                  'instagram_user', 'time_offset_minutes', 'time_offset_hours',
                  'tripadvisor_widget', 'latitude', 'longitude',
                  'delivery_type', 'delivery_link', 'quandoo_id',
                  'app_opening_times', 'firebase_id')


class RecipeStep(serializers.ModelSerializer):
    class Meta:
        model = models.RecipeStep
        fields = ('position', 'text')


class RecipeIngredient(serializers.ModelSerializer):
    description = NullCharField()
    unit_type = NullCharField()

    class Meta:
        model = models.RecipeIngredient
        fields = ('name', 'description', 'quantity', 'unit_type')


class Recipe(serializers.ModelSerializer):
    pg_id = serializers.SerializerMethodField('get_namespaced_id')
    ingredients = RecipeIngredient(many=True)
    steps = RecipeStep(many=True)

    def get_namespaced_id(self, obj):
        return obj.id

    class Meta:
        model = models.Recipe
        fields = ('pg_id', 'name', 'description', 'ingredients', 'steps')


class Dish(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dish-detail')
    pg_id = serializers.SerializerMethodField('get_namespaced_id')
    recipe = Recipe(read_only=True)
    restaurant = Restaurant(read_only=True)
    keywords = Keyword(many=True)

    def get_namespaced_id(self, obj):
        return obj.id

    class Meta:
        model = models.Dish
        fields = ('url', 'pg_id', 'recipe', 'restaurant', 'image_url', 'price', 'title',
                  'description', 'instagram_user', 'keywords', 'likes_count',
                  'views_count', 'firebase_id')
