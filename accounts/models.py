from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'owner', 'Shop Owner'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.OWNER,
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
