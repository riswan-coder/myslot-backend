from django.db import models
from accounts.models import User


class GamingCenter(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shops',
        limit_choices_to={'role': 'owner'},
    )

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    area = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    google_maps_url = models.URLField(
        blank=True,
        null=True
    )

    opening_time = models.TimeField()
    closing_time = models.TimeField()

    working_days = models.CharField(
        max_length=100,
        help_text="Comma-separated, e.g. Mon,Tue,Wed,Thu,Fri,Sat"
    )

    logo = models.ImageField(
        upload_to='shop_logos/',
        blank=True,
        null=True
    )

    cover_image = models.ImageField(
        upload_to='shop_covers/',
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
    )

    is_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name