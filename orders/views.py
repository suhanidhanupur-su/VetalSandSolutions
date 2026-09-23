import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from products.models import Product
from payments.models import Payment
from payments.services import calculate_items_amount, calculate_order_amount
from payments.views import _razorpay_client
from core.email_notifications import send_order_request_email

from .forms import CheckoutForm
from .models import Order, OrderItem

logger = logging.getLogger(__name__)


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

	is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

	if request.method == 'POST':
		form = CheckoutForm(request.POST)
		current_items, invalid_current_cart = _get_checkout_items(request)
		if invalid_current_cart or not current_items:
			msg = 'Your cart changed or items are no longer available. Please review your cart.'
			if is_ajax:
				return JsonResponse({'success': False, 'message': msg, 'redirect_url': reverse('cart_detail')}, status=400)
			messages.error(request, msg)
			return redirect('cart_detail')

		current_total = calculate_items_amount(current_items)

		if form.is_valid():
			payment_method = form.cleaned_data['payment_method']

			if payment_method == Order.PaymentMethod.ONLINE:
				# 1. Check pricing availability
				if current_total is None or current_total <= 0:
					msg = 'Online payment is currently unavailable for this order because pricing has not been configured.'
					if is_ajax:
						return JsonResponse({'success': False, 'message': msg}, status=400)
					form.add_error('payment_method', msg)
				# 2. Check Razorpay configuration
				elif not getattr(settings, 'RAZORPAY_CONFIGURED', False):
					msg = 'Online payment is temporarily unavailable. Please choose Cash on Delivery or contact us.'
					if is_ajax:
						return JsonResponse({'success': False, 'message': msg}, status=503)
					form.add_error('payment_method', msg)
				else:
					client = _razorpay_client()
					if client is None:
						msg = 'Online payment gateway is temporarily unavailable. Please choose Cash on Delivery or contact us.'
						if is_ajax:
							return JsonResponse({'success': False, 'message': msg}, status=503)
						form.add_error('payment_method', msg)
					else:
						# 3. Create or reuse pending unpaid order for this checkout session
						pending_order_id = request.session.get('pending_payment_order_id')
						order = None
						if pending_order_id:
							order = Order.objects.filter(
								id=pending_order_id,
								user=request.user,
								status=Order.Status.PENDING,
								payment_method=Order.PaymentMethod.ONLINE,
							).first()

						with transaction.atomic():
							if order is None:
								order = form.save(commit=False)
								order.user = request.user
								order.total_amount = current_total
								order.payment_method = Order.PaymentMethod.ONLINE
								order.status = Order.Status.PENDING
								order.save()
							else:
								for field in ('full_name', 'email', 'phone', 'address', 'city', 'state', 'pincode', 'notes'):
									setattr(order, field, form.cleaned_data[field])
								order.total_amount = current_total
								order.save()

							order.items.all().delete()
							OrderItem.objects.bulk_create(
								[
									OrderItem(
										order=order,
										product=item['product'],
										quantity=item['quantity'],
										unit_price=item['product'].price,
									)
									for item in current_items
								]
							)

							payment, _ = Payment.objects.get_or_create(order=order)
							payment.amount = current_total
							payment.payment_status = Payment.Status.PENDING
							payment.save()

						# 4. Create Razorpay order
						try:
							razorpay_order = client.order.create({
								'amount': int(current_total * 100),
								'currency': settings.RAZORPAY_CURRENCY,
								'receipt': f'order_{order.id}',
							})
						except Exception as exc:
							logger.warning('Razorpay order creation failed for order %s: %s', order.id, exc)
							msg = 'Unable to initialize online payment with gateway. Please try again or choose Cash on Delivery.'
							if is_ajax:
								return JsonResponse({'success': False, 'message': msg}, status=502)
							form.add_error('payment_method', msg)
						else:
							payment.payment_id = razorpay_order['id']
							payment.payment_status = Payment.Status.CREATED
							payment.save(update_fields=['payment_id', 'payment_status', 'updated_at'])

							request.session['pending_payment_order_id'] = order.id
							request.session.modified = True

							if is_ajax:
								return JsonResponse({
									'success': True,
									'payment_method': 'online',
									'order_id': order.id,
									'razorpay_order_id': razorpay_order['id'],
									'key_id': settings.RAZORPAY_KEY_ID,
									'amount': int(current_total * 100),
									'currency': settings.RAZORPAY_CURRENCY,
									'prefill': {
										'name': order.full_name,
										'email': order.email,
										'contact': order.phone,
									},
									'description': f'Order #{order.id}',
								})

							# Non-AJAX fallback
							return redirect('order_success', order_id=order.id)

			else:
				# Cash on Delivery (COD) Flow
				with transaction.atomic():
					order = form.save(commit=False)
					order.user = request.user
					order.total_amount = current_total
					order.payment_method = Order.PaymentMethod.COD
					order.status = Order.Status.PENDING
					order.save()
					Payment.objects.create(
						order=order,
						payment_status=Payment.Status.PENDING,
						amount=current_total,
					)
					OrderItem.objects.bulk_create(
						[
							OrderItem(
								order=order,
								product=item['product'],
								quantity=item['quantity'],
								unit_price=item['product'].price,
							)
							for item in current_items
						]
					)

					request.session['cart'] = {}
					request.session.pop('pending_payment_order_id', None)
					request.session.modified = True

				send_order_request_email(order)
				messages.success(request, f'Order #{order.id} has been submitted successfully.')

				if is_ajax:
					return JsonResponse({
						'success': True,
						'payment_method': 'cod',
						'redirect_url': reverse('order_success', args=[order.id]),
					})
				return redirect('order_success', order_id=order.id)

		else:
			if is_ajax:
				return JsonResponse({'success': False, 'errors': form.errors}, status=400)

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
		'cart_total': calculate_items_amount(cart_items),
		'payment_available': calculate_items_amount(cart_items) is not None,
		'razorpay_configured': getattr(settings, 'RAZORPAY_CONFIGURED', False),
	}
	return render(request, 'orders/checkout.html', context)


@login_required(login_url='login')
def order_success(request, order_id):
	order = get_object_or_404(
		Order.objects.select_related('payment').prefetch_related('items__product'),
		id=order_id,
		user=request.user,
	)
	order_total = calculate_order_amount(order)
	payment_ready = bool(
		getattr(order, 'payment', None)
		and order.payment_method == Order.PaymentMethod.ONLINE
		and order_total is not None
		and order.payment.payment_status != Payment.Status.PAID
		and getattr(settings, 'RAZORPAY_CONFIGURED', False)
	)
	return render(request, 'orders/order_success.html', {
		'order': order,
		'order_total': order_total,
		'pricing_available': order_total is not None,
		'payment_ready': payment_ready,
	})


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
