import logging
from django.db import DatabaseError, OperationalError, ProgrammingError
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Category, Product, Wishlist

logger = logging.getLogger(__name__)


def product_list(request):
    search_query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()
    selected_grade = request.GET.get('grade', '').strip()

    try:
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

        products = list(products.prefetch_related('images').order_by('-created_at'))

        wishlist_product_ids = set()
        if request.user.is_authenticated:
            wishlist_product_ids = set(
                Wishlist.objects.filter(user=request.user, product__in=products).values_list('product_id', flat=True)
            )

        for product in products:
            product.primary_image = product.images.filter(is_primary=True).first() or product.images.first()

        categories = list(Category.objects.filter(is_active=True).order_by('name'))
        grades = list(
            Product.objects.filter(is_active=True)
            .exclude(grade__exact='')
            .values_list('grade', flat=True)
            .distinct()
            .order_by('grade')
        )
    except (DatabaseError, OperationalError, ProgrammingError) as exc:
        logger.warning("Database tables unmigrated in product_list: %s", exc)
        products = []
        categories = []
        grades = []
        wishlist_product_ids = set()

    context = {
        'products': products,
        'categories': categories,
        'grades': grades,
        'search_query': search_query,
        'selected_category': selected_category,
        'selected_grade': selected_grade,
        'wishlist_product_ids': wishlist_product_ids,
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

    is_in_wishlist = request.user.is_authenticated and Wishlist.objects.filter(
        user=request.user, product=product
    ).exists()

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
        'is_in_wishlist': is_in_wishlist,
    }
    return render(request, 'products/product_detail.html', context)


@login_required(login_url='login')
def wishlist_detail(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related(
        'product__category'
    ).prefetch_related('product__images')

    for wishlist_item in wishlist_items:
        product = wishlist_item.product
        product.primary_image = product.images.filter(is_primary=True).first() or product.images.first()

    return render(request, 'products/wishlist.html', {'wishlist_items': wishlist_items})


@login_required(login_url='login')
@require_POST
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    Wishlist.objects.get_or_create(user=request.user, product=product)
    return redirect(request.META.get('HTTP_REFERER') or 'wishlist_detail')


@login_required(login_url='login')
@require_POST
def remove_from_wishlist(request, product_id):
    Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
    return redirect(request.META.get('HTTP_REFERER') or 'wishlist_detail')
