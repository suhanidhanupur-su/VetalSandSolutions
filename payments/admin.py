from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ('order', 'payment_id', 'payment_status', 'amount', 'created_at')
	list_filter = ('payment_status', 'created_at')
	search_fields = ('payment_id', 'order__id', 'order__full_name', 'order__email')
	ordering = ('-created_at',)
