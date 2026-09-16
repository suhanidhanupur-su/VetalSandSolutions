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
    return order.total_amount
