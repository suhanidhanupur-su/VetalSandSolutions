from cloudinary.models import CloudinaryField
from django.db import models


class GalleryImage(models.Model):
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	image = CloudinaryField('image')
	category = models.CharField(max_length=100, blank=True)
	alt_text = models.CharField(max_length=200, blank=True)
	is_active = models.BooleanField(default=True)
	display_order = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['display_order', '-created_at']
		verbose_name = 'Gallery image'
		verbose_name_plural = 'Gallery images'

	def __str__(self):
		return self.title
