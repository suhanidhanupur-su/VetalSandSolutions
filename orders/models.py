from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from products.models import Product


class Order(models.Model):
	class Status(models.TextChoices):
		PENDING = 'pending', 'Pending'
		CONFIRMED = 'confirmed', 'Confirmed'
		PROCESSING = 'processing', 'Processing'
		SHIPPED = 'shipped', 'Shipped'
		DELIVERED = 'delivered', 'Delivered'
		CANCELLED = 'cancelled', 'Cancelled'

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
	full_name = models.CharField(max_length=150)
	email = models.EmailField()
	phone = models.CharField(max_length=30)
	address = models.TextField()
	city = models.CharField(max_length=100)
	state = models.CharField(max_length=100)
	pincode = models.CharField(max_length=20)
	notes = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'Order #{self.pk} - {self.full_name}'


class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at']

	def __str__(self):
		return f'{self.product.name} x {self.quantity}'
