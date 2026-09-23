from decimal import Decimal
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from orders.models import Order
from orders.models import OrderItem
from products.models import Category, Product

from .models import Payment


class PaymentModelTests(TestCase):
	def setUp(self):
		user = get_user_model().objects.create_user(username='payment-user')
		self.order = Order.objects.create(
			user=user,
			full_name='Payment Customer',
			email='payment@example.com',
			phone='1234567890',
			address='Industrial Estate',
			city='Pune',
			state='Maharashtra',
			pincode='411001',
		)

	def test_payment_defaults_to_pending_and_amount_is_optional(self):
		payment = Payment.objects.create(order=self.order)

		self.assertEqual(payment.payment_status, Payment.Status.PENDING)
		self.assertIsNone(payment.amount)
		self.assertEqual(str(payment), f'Payment for Order #{self.order.id} - Pending')

	def test_payment_stores_future_gateway_fields(self):
		payment = Payment.objects.create(
			order=self.order,
			payment_id='future-gateway-id',
			payment_status=Payment.Status.CREATED,
			amount=Decimal('1250.00'),
		)

		self.assertEqual(payment.payment_id, 'future-gateway-id')
		self.assertEqual(payment.payment_status, 'Created')
		self.assertEqual(payment.amount, Decimal('1250.00'))

	def test_payment_is_registered_in_admin(self):
		self.assertIn(Payment, admin.site._registry)
		self.assertIn('payment_status', admin.site._registry[Payment].list_filter)

	def test_razorpay_creation_refuses_missing_amount(self):
		self.order.payment_method = Order.PaymentMethod.ONLINE
		self.order.save(update_fields=['payment_method'])
		category = Category.objects.create(name='Industrial', slug='industrial')
		product = Product.objects.create(category=category, name='Unpriced', slug='unpriced')
		OrderItem.objects.create(order=self.order, product=product, quantity=1)
		self.client.force_login(self.order.user)

		response = self.client.post(
			f'/orders/{self.order.id}/razorpay/create/',
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn('currently unavailable for this order', response.json()['message'])
		self.assertEqual(Payment.objects.get(order=self.order).payment_status, Payment.Status.PENDING)

	@patch('payments.views._razorpay_client')
	@patch('payments.views.settings')
	def test_razorpay_amount_comes_from_product_price(self, settings_mock, client_factory):
		category = Category.objects.create(name='Priced', slug='priced')
		product = Product.objects.create(
			category=category,
			name='Priced Product',
			slug='priced-product',
			price=1250,
		)
		OrderItem.objects.create(order=self.order, product=product, quantity=2)
		self.order.payment_method = Order.PaymentMethod.ONLINE
		self.order.total_amount = Decimal('2500.00')
		self.order.save(update_fields=['payment_method', 'total_amount'])
		settings_mock.RAZORPAY_TEST_MODE = True
		settings_mock.RAZORPAY_KEY_ID = 'rzp_test_example'
		settings_mock.RAZORPAY_KEY_SECRET = 'test_secret'
		settings_mock.RAZORPAY_CURRENCY = 'INR'
		client_factory.return_value.order.create.return_value = {'id': 'order_test_123'}
		self.client.force_login(self.order.user)

		response = self.client.post(f'/orders/{self.order.id}/razorpay/create/')

		self.assertEqual(response.status_code, 200)
		client_factory.return_value.order.create.assert_called_once_with({
			'amount': 250000,
			'currency': 'INR',
			'receipt': f'order_{self.order.id}',
		})
		self.assertEqual(Payment.objects.get(order=self.order).amount, Decimal('2500'))

	def test_razorpay_creation_refuses_another_users_order(self):
		other_user = get_user_model().objects.create_user(username='another-user')
		self.client.force_login(other_user)

		response = self.client.post(
			f'/orders/{self.order.id}/razorpay/create/',
		)

		self.assertEqual(response.status_code, 404)

	def test_missing_verification_fields_fail_payment(self):
		self.order.payment_method = Order.PaymentMethod.ONLINE
		self.order.save(update_fields=['payment_method'])
		payment = Payment.objects.create(order=self.order, payment_id='order_test_123')
		self.client.force_login(self.order.user)

		response = self.client.post(f'/orders/{self.order.id}/razorpay/verify/', {})

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json()['success'], False)
		self.assertEqual(Payment.objects.get(pk=payment.pk).payment_status, Payment.Status.FAILED)

	def test_payment_failed_requires_post(self):
		Payment.objects.create(order=self.order)
		self.client.force_login(self.order.user)

		get_response = self.client.get(f'/orders/{self.order.id}/payment-failed/')
		post_response = self.client.post(f'/orders/{self.order.id}/payment-failed/')

		self.assertEqual(get_response.status_code, 405)
		self.assertEqual(post_response.status_code, 302)
		self.assertEqual(Payment.objects.get(order=self.order).payment_status, Payment.Status.FAILED)

	@patch('payments.views._razorpay_client')
	@override_settings(
		EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
		DEFAULT_FROM_EMAIL='no-reply@example.com',
	)
	def test_valid_signature_marks_payment_paid_and_confirms_order(self, client_factory):
		self.order.payment_method = Order.PaymentMethod.ONLINE
		self.order.save(update_fields=['payment_method'])
		payment = Payment.objects.create(order=self.order, payment_id='order_test_123')
		client = client_factory.return_value
		self.client.force_login(self.order.user)

		session = self.client.session
		session['cart'] = {'1': 2}
		session['pending_payment_order_id'] = self.order.id
		session.save()

		response = self.client.post(
			f'/orders/{self.order.id}/razorpay/verify/',
			{
				'razorpay_payment_id': 'pay_test_123',
				'razorpay_order_id': payment.payment_id,
				'razorpay_signature': 'signature',
			},
		)

		client.utility.verify_payment_signature.assert_called_once()
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()['success'])
		payment.refresh_from_db()
		self.order.refresh_from_db()
		self.assertEqual(payment.payment_id, 'pay_test_123')
		self.assertEqual(payment.payment_status, Payment.Status.PAID)
		self.assertEqual(self.order.status, Order.Status.CONFIRMED)
		self.assertEqual(self.client.session.get('cart'), {})
		self.assertNotIn('pending_payment_order_id', self.client.session)
		from django.core import mail
		self.assertEqual(len(mail.outbox), 1)
		self.assertEqual(mail.outbox[0].to, ['payment@example.com'])

		second_response = self.client.post(
			f'/orders/{self.order.id}/razorpay/verify/',
			{
				'razorpay_payment_id': 'pay_test_123',
				'razorpay_order_id': payment.payment_id,
				'razorpay_signature': 'signature',
			},
		)
		self.assertEqual(second_response.status_code, 400)
		self.assertEqual(len(mail.outbox), 1)

	def test_razorpay_settings_aliases_and_cleaning(self):
		import os
		from unittest.mock import patch
		from config.settings import _get_first_env

		with patch.dict(os.environ, {'RAZORPAY_KEY_ID': '', 'RAZORPAY_KEY': ' "rzp_test_from_alias" '}, clear=False):
			resolved = _get_first_env('RAZORPAY_KEY_ID', 'RAZORPAY_KEY')
			self.assertEqual(resolved, 'rzp_test_from_alias')

		with patch.dict(os.environ, {'RAZORPAY_KEY_ID': 'value'}, clear=False):
			resolved_placeholder = _get_first_env('RAZORPAY_KEY_ID')
			self.assertEqual(resolved_placeholder, '')

