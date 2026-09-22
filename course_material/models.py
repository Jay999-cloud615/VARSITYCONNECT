from django.db import models
from django.contrib.auth.models import User


class Resource(models.Model):
	CATEGORY_CHOICES = [
		('TEXTBOOKS', 'Textbooks'),
		('NOTES', 'Lecture Notes'),
		('PAST_PAPERS', 'Past Papers'),
		('OTHER', 'Other'),
	]

	title = models.CharField(max_length=200)
	category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
	pdf_file = models.FileField(upload_to='uploads/pdfs/')
	uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.title
