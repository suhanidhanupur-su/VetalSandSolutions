from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from products.models import Product
from payments.models import Payment
from payments.services import calculate_items_amount, calculate_order_amount

from .forms import CheckoutForm
from .models import Order, OrderItem


def _get_checkout_items(request):
	cart = request.session.get('cart', {})
	cart_items = []
	product_ids = []
	invalid_cart = False

	for raw_product_id, raw_quantity in cart.items():
		try:
			product_id = int(raw_product_id)
			quantity = int(raw_quantity)
		except (TypeError, ValueError):
			invalid_cart = True
			continue

		if product_id <= 0 or quantity <= 0:
			invalid_cart = True
			continue

		product_ids.append(product_id)
		cart_items.append({'product_id': product_id, 'quantity': quantity})

	products = Product.objects.filter(id__in=product_ids, is_active=True).select_related('category')
	product_map = {product.id: product for product in products}

	for item in cart_items:
		product = product_map.get(item['product_id'])
		if product is None:
			invalid_cart = True
			continue
		item['product'] = product

	return [item for item in cart_items if 'product' in item], invalid_cart


@login_required(login_url='login')
def checkout(request):
	cart_items, invalid_cart = _get_checkout_items(request)
	if invalid_cart or not cart_items:
		if invalid_cart:
			messages.error(request, 'One or more products in your cart are no longer available.')
		else:
			messages.info(request, 'Add products to your cart before checking out.')
		return redirect('cart_detail')

	if request.method == 'POST':
		form = CheckoutForm(request.POST)
		if form.is_valid():
			with transaction.atomic():
				current_items, invalid_current_cart = _get_checkout_items(request)
				if invalid_current_cart or not current_items:
					messages.error(request, 'Your cart changed. Please review it before placing the order.')
					return redirect('cart_detail')

				order = form.save(commit=False)
				order.user = request.user
				order.save()
				Payment.objects.create(order=order)
				OrderItem.objects.bulk_create(
					[
						OrderItem(order=order, product=item['product'], quantity=item['quantity'])
						for item in current_items
					]
				)

				request.session['cart'] = {}
				request.session.modified = True

			messages.success(request, f'Order #{order.id} has been submitted successfully.')
			return redirect('order_success', order_id=order.id)
	else:
		form = CheckoutForm(initial={
			'full_name': request.user.get_full_name(),
			'email': request.user.email,
			'payment_method': Order.PaymentMethod.COD,
		})

	context = {
		'form': form,
		'cart_items': cart_items,
		'cart_count': sum(item['quantity'] for item in cart_items),
		'payment_available': calculate_items_amount(cart_items) is not None,
	}
	return render(request, 'orders/checkout.html', context)


@login_required(login_url='login')
def order_success(request, order_id):
	order = get_object_or_404(
		Order.objects.select_related('payment').prefetch_related('items__product'),
		id=order_id,
		user=request.user,
	)
	payment_ready = bool(
		getattr(order, 'payment', None)
		and order.payment_method == Order.PaymentMethod.RAZORPAY
		and calculate_order_amount(order) is not None
		and order.payment.payment_status != Payment.Status.PAID
		and getattr(settings, 'RAZORPAY_TEST_MODE', False)
		and getattr(settings, 'RAZORPAY_KEY_ID', '').startswith('rzp_test_')
	)
	return render(request, 'orders/order_success.html', {'order': order, 'payment_ready': payment_ready})


@login_required(login_url='login')
def order_list(request):
	orders = Order.objects.filter(user=request.user).annotate(item_count=Count('items'))
	return render(request, 'orders/order_list.html', {'orders': orders})


@login_required(login_url='login')
def order_detail(request, order_id):
	order = get_object_or_404(
		Order.objects.prefetch_related('items__product'),
		id=order_id,
		user=request.user,
	)
	return render(request, 'orders/order_detail.html', {'order': order})
