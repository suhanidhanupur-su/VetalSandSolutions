from django.shortcuts import render

from .models import Product


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')

    for product in products:
        product.primary_image = product.images.filter(is_primary=True).first() or product.images.first()

    return render(request, 'products/product_list.html', {'products': products})
