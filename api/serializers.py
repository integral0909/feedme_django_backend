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
