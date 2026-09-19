from django.contrib import admin
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Category, Product, ProductImage, Wishlist


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('product__name', 'alt_text')

    def save_model(self, request, obj, form, change):
        if not change or 'image' in form.changed_data:
            if not getattr(settings, 'CLOUDINARY_CONFIGURED', False):
                raise ValidationError(
                    'Cloudinary image uploads are unavailable. Configure the Cloudinary environment variables first.'
                )
        super().save_model(request, obj, form, change)


def _has_new_product_image(formset):
    return any(
        form.cleaned_data.get('image')
        for form in formset.forms
        if form.is_valid() and not form.cleaned_data.get('DELETE') and 'image' in form.changed_data
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'grade', 'price', 'is_active', 'is_featured', 'created_at')
    fields = (
        'category',
        'name',
        'slug',
        'short_description',
        'description',
        'grade',
        'price',
        'specifications',
        'applications',
        'industries',
        'is_active',
        'is_featured',
    )
    list_filter = ('category', 'is_active', 'is_featured', 'grade')
    search_fields = ('name', 'grade', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]

    def save_formset(self, request, form, formset, change):
        if formset.model is ProductImage and _has_new_product_image(formset):
            if not getattr(settings, 'CLOUDINARY_CONFIGURED', False):
                raise ValidationError(
                    'Cloudinary image uploads are unavailable. Configure the Cloudinary environment variables first.'
                )
        super().save_formset(request, form, formset, change)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'product__name')
    date_hierarchy = 'created_at'
