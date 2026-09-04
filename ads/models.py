from django.db import models


class Advertisement(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to='ads/')
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title