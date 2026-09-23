from products.models import Product


def cart_count(request):
    cart = request.session.get('cart', {})
    total_items = 0
    product_ids = {
        int(product_id)
        for product_id in cart
        if str(product_id).isdigit()
    }
    active_product_ids = set(
        Product.objects.filter(id__in=product_ids, is_active=True).values_list('id', flat=True)
    )

    for product_id, quantity in cart.items():
        if not str(product_id).isdigit() or int(product_id) not in active_product_ids:
            continue
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue
        if quantity > 0:
            total_items += quantity

    return {'cart_count': total_items}

