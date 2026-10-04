from django.db import models
from django.contrib.auth.models import User

class Accommodation(models.Model):
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=255)  # e.g., "De Korte St, Braamfontein"
    price_per_month = models.DecimalField(max_digits=8, decimal_places=2)
    amenities = models.CharField(max_length=255, help_text="e.g., Wifi, Furnished, Own bathroom")
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='uploads/accommodations/', blank=True, null=True)
    landlord = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Job(models.Model):
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=255)
    pay = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title