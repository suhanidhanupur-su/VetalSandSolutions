from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	fields = ('product', 'quantity', 'created_at')
	readonly_fields = ('created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'full_name', 'email', 'status', 'created_at')
	list_filter = ('status', 'created_at')
	search_fields = ('full_name', 'email', 'user__username')
	ordering = ('-created_at',)
	inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ('order', 'product', 'quantity', 'created_at')
	list_filter = ('created_at',)
	search_fields = ('order__full_name', 'order__email', 'product__name')
	ordering = ('-created_at',)
