from django.db import models
from shops.models import GamingCenter


class Game(models.Model):
    shop = models.ForeignKey(
        GamingCenter,
        on_delete=models.CASCADE,
        related_name='games',
    )
    name = models.CharField(max_length=100)  # e.g. "PlayStation 5"
    category = models.CharField(max_length=100, blank=True)  # e.g. "Console"
    platform = models.CharField(max_length=100, blank=True)  # e.g. "PS5"
    image = models.ImageField(upload_to='game_images/', blank=True, null=True)
    description = models.TextField(blank=True)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} @ {self.shop.name}"
class Machine(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        MAINTENANCE = 'maintenance', 'Under Maintenance'
        DISABLED = 'disabled', 'Disabled'

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='machines',
    )
    machine_number = models.CharField(max_length=20)  # e.g. "PS5-01"
    name = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )

    class Meta:
        unique_together = ('game', 'machine_number')

    def __str__(self):
        return f"{self.machine_number} ({self.game.name})"