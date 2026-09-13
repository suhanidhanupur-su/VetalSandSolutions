from django.shortcuts import get_object_or_404, render

from .models import Product


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')

    for product in products:
        product.primary_image = product.images.filter(is_primary=True).first() or product.images.first()

    context = {'products': products}
    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'),
        slug=slug,
        is_active=True,
    )

    product.primary_image = product.images.filter(is_primary=True).first() or product.images.first()
    product_images = list(product.images.all())

    related_products = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(id=product.id)
        .select_related('category')
        .prefetch_related('images')[:4]
    )

    for related_product in related_products:
        related_product.primary_image = (
            related_product.images.filter(is_primary=True).first() or related_product.images.first()
        )

    context = {
        'product': product,
        'product_images': product_images,
        'related_products': related_products,
    }
    return render(request, 'products/product_detail.html', context)
