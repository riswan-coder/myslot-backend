from rest_framework import serializers
from .models import GamingCenter


class GamingCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = GamingCenter
        fields = '__all__'
        read_only_fields = ['owner', 'status']