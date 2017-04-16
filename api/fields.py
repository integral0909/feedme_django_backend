from rest_framework import serializers
import six


class NullCharField(serializers.CharField):
    def to_representation(self, value):
        return None if len(value) == 0 else six.text_type(value)
