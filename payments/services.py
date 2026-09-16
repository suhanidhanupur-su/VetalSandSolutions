from decimal import Decimal

def calculate_items_amount(items):
    total = Decimal('0.00')
    has_items = False

    for item in items:
        has_items = True
        product = item['product'] if isinstance(item, dict) else item.product
        quantity = item['quantity'] if isinstance(item, dict) else item.quantity
        if product.price is None or product.price <= 0:
            return None
        total += product.price * quantity

    return total if has_items and total > 0 else None


def calculate_order_amount(order):
    if order.total_amount is not None:
        return order.total_amount

    total = Decimal('0.00')
    has_items = False
    for item in order.items.select_related('product').all():
        has_items = True
        unit_price = item.unit_price if item.unit_price is not None else item.product.price
        if unit_price is None:
            return None
        total += Decimal(unit_price) * Decimal(item.quantity)

    return total if has_items else None
