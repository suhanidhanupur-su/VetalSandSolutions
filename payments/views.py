import logging

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from orders.models import Order

from .models import Payment
from .services import calculate_order_amount


logger = logging.getLogger(__name__)


def _razorpay_client():
	if (
		not settings.RAZORPAY_TEST_MODE
		or not settings.RAZORPAY_KEY_ID.startswith('rzp_test_')
		or not settings.RAZORPAY_KEY_SECRET
	):
		return None
	return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@login_required(login_url='login')
@require_POST
def create_razorpay_order(request, order_id):
	order = get_object_or_404(Order, id=order_id, user=request.user)
	if order.payment_method != Order.PaymentMethod.ONLINE:
		return JsonResponse({'success': False, 'message': 'Online payment is not selected for this order.'}, status=400)
	payment, _ = Payment.objects.get_or_create(order=order)
	if payment.payment_status == Payment.Status.PAID:
		return JsonResponse({'success': False, 'message': 'This order has already been paid.'}, status=400)
	amount = calculate_order_amount(order)

	if amount is None or amount <= 0:
		return JsonResponse(
			{'success': False, 'message': 'Online payment is currently unavailable for this order. Please contact us for pricing.'},
			status=400,
		)

	client = _razorpay_client()
	if client is None:
		return JsonResponse(
			{'success': False, 'message': 'Online payment is currently unavailable. Please contact us.'},
			status=503,
		)

	try:
		razorpay_order = client.order.create({
			'amount': int(amount * 100),
			'currency': settings.RAZORPAY_CURRENCY,
			'receipt': f'order_{order.id}',
		})
	except Exception as exc:
		logger.warning('Razorpay order creation failed for order_id=%s: %s', order.id, exc)
		return JsonResponse(
			{'success': False, 'message': 'Unable to start online payment. Please contact us.'},
			status=502,
		)

	order_id = razorpay_order.get('id')
	if not order_id:
		logger.warning('Razorpay order creation returned no order id for order_id=%s', order.id)
		return JsonResponse(
			{'success': False, 'message': 'Unable to start online payment. Please contact us.'},
			status=502,
		)

	payment.payment_id = order_id
	payment.payment_status = Payment.Status.CREATED
	payment.amount = amount
	payment.save(update_fields=['payment_id', 'payment_status', 'amount', 'updated_at'])
	return JsonResponse({
		'success': True,
		'key_id': settings.RAZORPAY_KEY_ID,
		'razorpay_order_id': razorpay_order['id'],
		'amount': int(amount * 100),
		'currency': settings.RAZORPAY_CURRENCY,
	})


@login_required(login_url='login')
@require_POST
def verify_payment(request, order_id):
	order = get_object_or_404(Order, id=order_id, user=request.user)
	if order.payment_method != Order.PaymentMethod.ONLINE:
		return JsonResponse({'success': False, 'message': 'Online payment is not selected for this order.'}, status=400)
	payment = get_object_or_404(Payment, order=order)
	if payment.payment_status == Payment.Status.PAID:
		return JsonResponse({'success': False, 'message': 'This order has already been paid.'}, status=400)
	payment_id = request.POST.get('razorpay_payment_id', '').strip()
	razorpay_order_id = request.POST.get('razorpay_order_id', '').strip()
	signature = request.POST.get('razorpay_signature', '').strip()

	if not payment_id or not razorpay_order_id or not signature:
		payment.payment_status = Payment.Status.FAILED
		payment.save(update_fields=['payment_status', 'updated_at'])
		return JsonResponse({'success': False, 'message': 'Payment verification could not be completed.'}, status=400)

	if razorpay_order_id != payment.payment_id:
		payment.payment_status = Payment.Status.FAILED
		payment.save(update_fields=['payment_status', 'updated_at'])
		return JsonResponse({'success': False, 'message': 'Payment verification could not be completed.'}, status=400)

	client = _razorpay_client()
	if client is None:
		return JsonResponse({'success': False, 'message': 'Payment verification is currently unavailable.'}, status=503)

	try:
		client.utility.verify_payment_signature({
			'razorpay_payment_id': payment_id,
			'razorpay_order_id': razorpay_order_id,
			'razorpay_signature': signature,
		})
	except Exception:
		payment.payment_status = Payment.Status.FAILED
		payment.save(update_fields=['payment_status', 'updated_at'])
		return JsonResponse({'success': False, 'message': 'Payment verification failed.'}, status=400)

	with transaction.atomic():
		payment.payment_id = payment_id
		payment.payment_status = Payment.Status.PAID
		payment.save(update_fields=['payment_id', 'payment_status', 'updated_at'])
		order.status = Order.Status.CONFIRMED
		order.save(update_fields=['status', 'updated_at'])

	return JsonResponse({'success': True, 'redirect_url': f'/orders/{order.id}/success/'})


@login_required(login_url='login')
@require_POST
def payment_failed(request, order_id):
	order = get_object_or_404(Order, id=order_id, user=request.user)
	Payment.objects.filter(
		order=order,
	).exclude(payment_status=Payment.Status.PAID).update(payment_status=Payment.Status.FAILED)
	messages.error(request, 'Payment was not completed. Your order remains pending.')
	return redirect('order_success', order_id=order.id)
