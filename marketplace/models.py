from django.db import models
from django.contrib.auth.models import User


class MarketplaceListing(models.Model):
	CATEGORY_CHOICES = [
		('textbooks', 'Textbooks'),
		('electronics', 'Electronics'),
		('furniture', 'Furniture'),
		('services', 'Services'),
	]

	title = models.CharField(max_length=200)
	image = models.ImageField(upload_to='uploads/marketplace/', blank=True, null=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)  # Supports prices like R450 or R150/hr
	quantity_available = models.PositiveIntegerField(default=1, verbose_name='Quantity available')
	price_suffix = models.CharField(max_length=20, blank=True, null=True)  # e.g., '/hr' if applicable
	category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
	condition = models.CharField(max_length=100, default='Like new')
	description = models.TextField()

	# Seller information
	seller = models.ForeignKey(User, on_delete=models.CASCADE)
	seller_rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
	seller_sales_count = models.IntegerField(default=0)

	# Location & metadata
	location = models.CharField(max_length=100, default='On campus')
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.title