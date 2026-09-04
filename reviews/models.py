from django.db import models
from accounts.models import User
from shops.models import GamingCenter
from bookings.models import Booking


class Review(models.Model):
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='review',
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    shop = models.ForeignKey(GamingCenter, on_delete=models.CASCADE, related_name='reviews')
    guest_name = models.CharField(max_length=100, blank=True)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    is_flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.guest_name or self.user} → {self.shop.name} ({self.rating}★)"