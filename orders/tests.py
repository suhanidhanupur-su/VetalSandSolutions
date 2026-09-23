from decimal import Decimal
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from products.models import Category, Product

from .models import Order, OrderItem
from payments.models import Payment


class OrderFlowTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(
			username='order-user',
			email='order@example.com',
			password='Strong-order-password-123!',
		)
		self.other_user = user_model.objects.create_user(
			username='other-user',
			email='other@example.com',
			password='Strong-other-password-123!',
		)
		self.category = Category.objects.create(name='Industrial', slug='industrial')
		self.product = Product.objects.create(
			category=self.category,
			name='Foundry Sand',
			slug='foundry-sand',
			short_description='Consistent silica sand for foundry applications.',
			grade='F60',
			is_active=True,
		)
		self.second_product = Product.objects.create(
			category=self.category,
			name='Glass Sand',
			slug='glass-sand',
			is_active=True,
		)

	def _set_cart(self, items):
		session = self.client.session
		session['cart'] = {str(product_id): quantity for product_id, quantity in items.items()}
		session.save()

	def _checkout_data(self):
		return {
			'full_name': 'Order Customer',
			'email': 'customer@example.com',
			'phone': '+91 9876543210',
			'address': 'Industrial Estate, Plot 12',
			'city': 'Pune',
			'state': 'Maharashtra',
			'pincode': '411001',
			'notes': 'Please share B2B pricing details.',
			'payment_method': Order.PaymentMethod.COD,
		}

	def test_logged_out_checkout_redirects_to_login_with_next(self):
		response = self.client.get(reverse('checkout'))

		self.assertRedirects(
			response,
			f'{reverse("login")}?next={reverse("checkout")}',
		)

	def test_empty_cart_redirects_to_cart(self):
		self.client.force_login(self.user)

		response = self.client.get(reverse('checkout'))

		self.assertRedirects(response, reverse('cart_detail'))
		self.assertEqual(response.wsgi_request.session.get('cart', {}), {})

	def test_checkout_opens_with_products_in_cart(self):
		self.client.force_login(self.user)
		self._set_cart({self.product.id: 1})

		response = self.client.get(reverse('checkout'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Checkout')
		self.assertContains(response, self.product.name)
		self.assertContains(response, 'Cash on Delivery')
		self.assertContains(response, 'Online Payment')

	def test_checkout_form_validates_required_fields(self):
		self.client.force_login(self.user)
		self._set_cart({self.product.id: 2})

		response = self.client.post(reverse('checkout'), {'email': 'invalid-only@example.com'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'This field is required.')
		self.assertEqual(Order.objects.count(), 0)
		self.assertEqual(self.client.session['cart'], {str(self.product.id): 2})

	@override_settings(
		EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
		DEFAULT_FROM_EMAIL='no-reply@example.com',
	)
	def test_successful_checkout_creates_order_items_and_clears_cart(self):
		self.client.force_login(self.user)
		self._set_cart({self.product.id: 2, self.second_product.id: 1})

		response = self.client.post(reverse('checkout'), self._checkout_data())

		order = Order.objects.get(user=self.user)
		self.assertRedirects(response, reverse('order_success', args=[order.id]))
		self.assertEqual(order.full_name, 'Order Customer')
		self.assertEqual(order.status, Order.Status.PENDING)
		self.assertEqual(order.payment_method, Order.PaymentMethod.COD)
		self.assertEqual(
			set(order.items.values_list('product_id', 'quantity')),
			{(self.product.id, 2), (self.second_product.id, 1)},
		)
		self.assertEqual(self.client.session['cart'], {})
		self.assertTrue(Payment.objects.filter(order=order, payment_status=Payment.Status.PENDING).exists())
		from django.core import mail
		self.assertEqual(len(mail.outbox), 1)
		self.assertEqual(mail.outbox[0].to, ['customer@example.com'])

		success_response = self.client.get(reverse('order_success', args=[order.id]))
		self.assertContains(success_response, f'#{order.id}')
		self.assertContains(success_response, 'B2B pricing')
		self.assertContains(success_response, 'Online payment is currently unavailable')
		self.assertNotContains(success_response, 'Pay with Razorpay')

	def test_online_payment_selection_stays_pending_without_verified_amount(self):
		self.client.force_login(self.user)
		self._set_cart({self.product.id: 1})
		checkout_data = self._checkout_data()
		checkout_data['payment_method'] = Order.PaymentMethod.ONLINE

		response = self.client.post(reverse('checkout'), checkout_data)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Online payment is currently unavailable for this order because pricing has not been configured.')
		self.assertEqual(Order.objects.count(), 0)
		self.assertEqual(self.client.session['cart'], {str(self.product.id): 1})

	@override_settings(RAZORPAY_CONFIGURED=False)
	def test_online_payment_refuses_when_razorpay_unconfigured(self):
		self.product.price = Decimal('100.00')
		self.product.save(update_fields=['price'])
		self.client.force_login(self.user)
		self._set_cart({self.product.id: 1})
		checkout_data = self._checkout_data()
		checkout_data['payment_method'] = Order.PaymentMethod.ONLINE

		# Normal POST
		response = self.client.post(reverse('checkout'), checkout_data)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Online payment is temporarily unavailable. Please choose Cash on Delivery or contact us.')
		self.assertEqual(Order.objects.count(), 0)
		self.assertEqual(self.client.session['cart'], {str(self.product.id): 1})

		# AJAX POST
		ajax_response = self.client.post(
			reverse('checkout'),
			checkout_data,
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(ajax_response.status_code, 503)
		self.assertFalse(ajax_response.json()['success'])
		self.assertIn('Online payment is temporarily unavailable', ajax_response.json()['message'])
		self.assertEqual(Order.objects.count(), 0)

	@patch('orders.views._razorpay_client')
	@override_settings(
		RAZORPAY_CONFIGURED=True,
		RAZORPAY_KEY_ID='rzp_test_mock_123',
		RAZORPAY_KEY_SECRET='mock_secret',
		RAZORPAY_CURRENCY='INR',
	)
	def test_online_payment_ajax_creates_order_and_reuses_on_retry(self, client_factory):
		mock_client = client_factory.return_value
		mock_client.order.create.return_value = {'id': 'order_rzp_mock_123'}

		self.product.price = Decimal('250.00')
		self.product.save(update_fields=['price'])
		self.client.force_login(self.user)
		self._set_cart({self.product.id: 2})
		checkout_data = self._checkout_data()
		checkout_data['payment_method'] = Order.PaymentMethod.ONLINE

		# 1. First AJAX submission
		response = self.client.post(
			reverse('checkout'),
			checkout_data,
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertTrue(data['success'])
		self.assertEqual(data['razorpay_order_id'], 'order_rzp_mock_123')
		self.assertEqual(data['key_id'], 'rzp_test_mock_123')
		self.assertEqual(data['amount'], 50000)  # 2 * 250 = 500 => 50000 paise

		self.assertEqual(Order.objects.count(), 1)
		order = Order.objects.first()
		self.assertEqual(order.status, Order.Status.PENDING)
		self.assertEqual(order.total_amount, Decimal('500.00'))
		# Cart must NOT be cleared yet
		self.assertEqual(self.client.session['cart'], {str(self.product.id): 2})
		self.assertEqual(self.client.session.get('pending_payment_order_id'), order.id)

		# 2. Retry submission (e.g. user dismissed or retried payment) - must reuse same order, no duplicates!
		retry_response = self.client.post(
			reverse('checkout'),
			checkout_data,
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)
		self.assertEqual(retry_response.status_code, 200)
		self.assertEqual(Order.objects.count(), 1)
		self.assertEqual(retry_response.json()['order_id'], order.id)


	def test_priced_checkout_persists_total_and_item_price_snapshots(self):
		self.product.price = Decimal('125.00')
		self.product.save(update_fields=['price'])
		self.second_product.price = Decimal('80.00')
		self.second_product.save(update_fields=['price'])
		self.client.force_login(self.user)
		self._set_cart({self.product.id: 2, self.second_product.id: 1})

		response = self.client.post(reverse('checkout'), self._checkout_data())

		order = Order.objects.get(user=self.user)
		self.assertRedirects(response, reverse('order_success', args=[order.id]))
		self.assertEqual(order.total_amount, Decimal('330.00'))
		self.assertEqual(
			set(order.items.values_list('product_id', 'unit_price')),
			{(self.product.id, Decimal('125.00')), (self.second_product.id, Decimal('80.00'))},
		)

	def test_inactive_product_prevents_order_creation_and_preserves_cart(self):
		inactive_product = Product.objects.create(
			category=self.category,
			name='Archived Sand',
			slug='archived-sand',
			is_active=False,
		)
		self.client.force_login(self.user)
		self._set_cart({self.product.id: 1, inactive_product.id: 1})

		response = self.client.post(reverse('checkout'), self._checkout_data())

		self.assertRedirects(response, reverse('cart_detail'))
		self.assertEqual(Order.objects.count(), 0)
		self.assertEqual(
			self.client.session['cart'],
			{str(self.product.id): 1, str(inactive_product.id): 1},
		)

	def test_order_list_only_shows_logged_in_users_orders(self):
		own_order = Order.objects.create(user=self.user, **self._checkout_data())
		other_order = Order.objects.create(user=self.other_user, **self._checkout_data())
		OrderItem.objects.create(order=own_order, product=self.product, quantity=1)
		OrderItem.objects.create(order=other_order, product=self.second_product, quantity=3)
		self.client.force_login(self.user)

		response = self.client.get(reverse('order_list'))

		self.assertContains(response, f'Order #{own_order.id}')
		self.assertNotContains(response, f'Order #{other_order.id}')

	def test_order_detail_cannot_be_accessed_by_another_user(self):
		order = Order.objects.create(user=self.other_user, **self._checkout_data())
		OrderItem.objects.create(order=order, product=self.product, quantity=1)
		self.client.force_login(self.user)

		response = self.client.get(reverse('order_detail', args=[order.id]))

		self.assertEqual(response.status_code, 404)

	def test_order_success_and_detail_pages_open_for_owner(self):
		order = Order.objects.create(user=self.user, **self._checkout_data())
		OrderItem.objects.create(order=order, product=self.product, quantity=1)
		self.client.force_login(self.user)

		success_response = self.client.get(reverse('order_success', args=[order.id]))
		detail_response = self.client.get(reverse('order_detail', args=[order.id]))

		self.assertEqual(success_response.status_code, 200)
		self.assertEqual(detail_response.status_code, 200)
		self.assertContains(detail_response, self.product.name)

	def test_order_admin_and_inline_are_registered(self):
		self.assertIn(Order, admin.site._registry)
		self.assertIn(OrderItem, admin.site._registry)
		self.assertIn('status', admin.site._registry[Order].list_filter)
