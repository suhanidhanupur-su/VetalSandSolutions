from django.db import models

from orders.models import Order


class Payment(models.Model):
	class Status(models.TextChoices):
		PENDING = 'Pending', 'Pending'
		CREATED = 'Created', 'Created'
		PAID = 'Paid', 'Paid'
		FAILED = 'Failed', 'Failed'
		REFUNDED = 'Refunded', 'Refunded'

	order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
	payment_id = models.CharField(max_length=255, blank=True)
	payment_status = models.CharField(
		max_length=50,
		choices=Status.choices,
		default=Status.PENDING,
	)
	amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'Payment for Order #{self.order_id} - {self.payment_status}'
