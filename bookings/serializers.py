from rest_framework import serializers
from .models import Slot, Booking


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'booking_id', 'user', 'guest_name', 'guest_phone', 'slot', 'status', 'amount', 'created_at']
        read_only_fields = ['booking_id', 'status', 'amount', 'user']