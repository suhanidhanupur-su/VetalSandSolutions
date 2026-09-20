from django.contrib import admin
from django.utils.html import format_html

from .models import GalleryImage


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'is_active', 'display_order', 'created_at', 'image_preview')
	list_filter = ('category', 'is_active')
	search_fields = ('title', 'description', 'category')
	ordering = ('display_order', '-created_at')
	list_editable = ('is_active', 'display_order')
	readonly_fields = ('image_preview',)

	@admin.display(description='Preview')
	def image_preview(self, obj):
		if not obj.image:
			return '-'
		return format_html(
			'<img src="{}" alt="{}" style="width: 100px; height: 65px; object-fit: cover; border-radius: 4px;">',
			obj.image.url,
			obj.alt_text or obj.title,
		)
