def cart_count(request):
    cart = request.session.get('cart', {})
    total_items = 0

    for quantity in cart.values():
        try:
            total_items += int(quantity)
        except (TypeError, ValueError):
            continue

    return {'cart_count': total_items}
