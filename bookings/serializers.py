from rest_framework import serializers
from .models import Slot, Booking
from django.utils import timezone


class SlotSerializer(serializers.ModelSerializer):
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = Slot
        fields = ['id', 'machine', 'date', 'start_time', 'end_time', 'price', 'is_booked', 'is_locked']

    def get_is_locked(self, obj):
        return bool(obj.locked_until and obj.locked_until > timezone.now())

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'booking_id', 'user', 'guest_name', 'guest_phone', 'slot', 'status', 'amount', 'created_at']
        read_only_fields = ['booking_id', 'status', 'amount', 'user']