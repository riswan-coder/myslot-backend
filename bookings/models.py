from django.db import models
from games.models import Machine

from accounts.models import User
import uuid


class Slot(models.Model):
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='slots',
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('machine', 'date', 'start_time')
        ordering = ['date', 'start_time']

    def __str__(self):
        status = "Booked" if self.is_booked else "Available"
        return f"{self.machine} | {self.date} {self.start_time}-{self.end_time} ({status})"


class Booking(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    booking_id = models.CharField(max_length=30, unique=True, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='bookings',
        null=True,
        blank=True,
    )

    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=False)


    guest_name = models.CharField(max_length=100, blank=True)
    guest_phone = models.CharField(max_length=15, blank=True)
    slot = models.OneToOneField(
        Slot,
        on_delete=models.CASCADE,
        related_name='booking',
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.UPCOMING,
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.booking_id:
            date_str = self.slot.date.strftime('%Y%m%d')
            unique_part = str(uuid.uuid4().int)[:5]
            self.booking_id = f"MS-{date_str}-{unique_part}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.booking_id