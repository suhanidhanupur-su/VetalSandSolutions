from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import Product


def _get_cart(request):
    return request.session.get('cart', {})


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = _get_cart(request)

    try:
        quantity = int(request.POST.get('quantity', request.GET.get('quantity', 1)))
    except (TypeError, ValueError):
        quantity = 1

    if quantity <= 0:
        quantity = 1

    cart_key = str(product.id)
    cart[cart_key] = cart.get(cart_key, 0) + quantity
    request.session['cart'] = cart
    request.session.modified = True

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('product_list')


def cart_detail(request):
    cart = _get_cart(request)
    product_ids = [int(product_id) for product_id in cart.keys() if str(product_id).isdigit()]
    products = Product.objects.filter(id__in=product_ids, is_active=True).select_related('category').prefetch_related('images')
    product_map = {product.id: product for product in products}

    cart_items = []
    cart_count = 0

    for product_id, quantity in cart.items():
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if quantity <= 0:
            continue

        product = product_map.get(product_id)
        if product is None:
            continue

        product.primary_image = product.images.filter(is_primary=True).first() or product.images.first()
        cart_items.append({'product': product, 'quantity': quantity})
        cart_count += quantity

    context = {'cart_items': cart_items, 'cart_count': cart_count}
    return render(request, 'cart/cart_detail.html', context)


@require_POST
def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart_detail')


@require_POST
def update_cart(request, product_id):
    cart = _get_cart(request)

    try:
        quantity = int(request.POST.get('quantity', 0))
    except (TypeError, ValueError):
        quantity = 0

    if quantity <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = quantity

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart_detail')
