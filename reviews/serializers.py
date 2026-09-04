from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'shop', 'guest_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['shop', 'guest_name']