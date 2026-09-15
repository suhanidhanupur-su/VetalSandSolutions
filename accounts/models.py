from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	full_name = models.CharField(max_length=150, blank=True)
	phone_number = models.CharField(max_length=30, blank=True)
	profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

	def __str__(self):
		return f'{self.user.username} Profile'
