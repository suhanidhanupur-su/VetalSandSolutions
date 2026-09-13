from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def product_list(request):
    search_query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()
    selected_grade = request.GET.get('grade', '').strip()

    products = Product.objects.filter(is_active=True).select_related('category')

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(short_description__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    if selected_category:
        products = products.filter(category__slug=selected_category)

    if selected_grade:
        products = products.filter(grade=selected_grade)

    products = products.prefetch_related('images').order_by('-created_at')

    for product in products:
        product.primary_image = product.images.filter(is_primary=True).first() or product.images.first()

    categories = Category.objects.filter(is_active=True).order_by('name')
    grades = (
        Product.objects.filter(is_active=True)
        .exclude(grade__exact='')
        .values_list('grade', flat=True)
        .distinct()
        .order_by('grade')
    )

    context = {
        'products': products,
        'categories': categories,
        'grades': grades,
        'search_query': search_query,
        'selected_category': selected_category,
        'selected_grade': selected_grade,
    }
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
