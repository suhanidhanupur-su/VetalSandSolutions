import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
from products.models import Product

c = Client()
p = Product.objects.filter(is_active=True).first()
print('PRODUCT', p.id if p else None)
if p:
    add_response = c.get(f'/cart/add/{p.id}/')
    print('ADD_STATUS', add_response.status_code)
    print('ADD_SESSION', c.session.get('cart'))

    cart_response = c.get('/cart/')
    print('CART_STATUS', cart_response.status_code)
    print('CART_HAS_PRODUCT', 'Your cart is currently empty.' not in cart_response.content.decode('utf-8', 'ignore'))

    update_response = c.post(f'/cart/update/{p.id}/', {'quantity': 3})
    print('UPDATE_STATUS', update_response.status_code)
    print('UPDATE_SESSION', c.session.get('cart'))

    remove_response = c.post(f'/cart/remove/{p.id}/', {})
    print('REMOVE_STATUS', remove_response.status_code)
    print('REMOVE_SESSION', c.session.get('cart'))
