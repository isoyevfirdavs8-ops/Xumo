from rest_framework import serializers
from .models import AboutItem


class AboutItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutItem
        fields = ('id', 'title', 'content', 'position')
        read_only_fields = ('id',)
