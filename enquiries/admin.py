from django.contrib import admin

from .models import ContactEnquiry, QuoteRequest


@admin.register(ContactEnquiry)
class ContactEnquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone', 'created_at')
    search_fields = ('name', 'company', 'email', 'phone')
    list_filter = ('created_at',)


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone', 'product', 'grade', 'quantity', 'application', 'location', 'created_at')
    search_fields = ('name', 'company', 'email', 'phone', 'grade', 'application', 'location')
    list_filter = ('grade', 'application', 'location', 'created_at')
