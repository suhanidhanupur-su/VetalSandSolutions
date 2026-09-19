from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal

from django.contrib import admin
from django.test import TestCase

from cloudinary.models import CloudinaryField

from .admin import ProductImageInline
from .models import Category, Product, ProductImage


class ProductPriceTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(name='Industrial', slug='industrial')

	def test_price_is_optional_and_admin_exposes_it(self):
		product = Product.objects.create(
			category=self.category,
			name='Unpriced Sand',
			slug='unpriced-sand',
		)

		self.assertIsNone(product.price)
		self.assertIn('price', admin.site._registry[Product].list_display)
		self.assertEqual(
			Product._meta.get_field('price').help_text,
			'Enter the product price in INR. Leave blank if pricing is available only on request.',
		)

	def test_price_accepts_admin_entered_inr_value(self):
		product = Product.objects.create(
			category=self.category,
			name='Priced Sand',
			slug='priced-sand',
			price=Decimal('1250.00'),
		)

		self.assertEqual(product.price, Decimal('1250.00'))


class ProductImageIntegrationTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(name='Industrial', slug='industrial')
		self.product = Product.objects.create(
			category=self.category,
			name='Foundry Sand',
			slug='foundry-sand',
			is_active=True,
		)

	def test_product_image_uses_cloudinary_field_and_admin_inline(self):
		self.assertIsInstance(ProductImage._meta.get_field('image'), CloudinaryField)
		self.assertIs(ProductImageInline.model, ProductImage)
		self.assertIn(ProductImageInline, admin.site._registry[Product].inlines)

	def test_product_pages_show_placeholders_when_images_are_missing(self):
		list_response = self.client.get(reverse('product_list'))
		detail_response = self.client.get(reverse('product_detail', args=[self.product.slug]))
		home_response = self.client.get(reverse('home'))

		self.assertContains(list_response, 'No product image available')
		self.assertContains(detail_response, 'No product image available')
		self.assertContains(home_response, 'home-product-mark')

from .models import Category, Product, Wishlist


class WishlistTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(username='wishlist-user', password='test-password-123')
		self.category = Category.objects.create(name='Industrial', slug='industrial')
		self.product = Product.objects.create(
			category=self.category,
			name='Foundry Sand',
			slug='foundry-sand',
			short_description='Consistent silica sand for foundry applications.',
			grade='F60',
			is_active=True,
		)
		self.inactive_product = Product.objects.create(
			category=self.category,
			name='Archived Sand',
			slug='archived-sand',
			is_active=False,
		)

	def test_logged_out_user_is_redirected_to_login(self):
		response = self.client.get(reverse('wishlist_detail'))

		self.assertRedirects(response, f'{reverse("login")}?next={reverse("wishlist_detail")}')

		add_response = self.client.post(reverse('add_to_wishlist', args=[self.product.id]))

		self.assertRedirects(
			add_response,
			f'{reverse("login")}?next={reverse("add_to_wishlist", args=[self.product.id])}',
		)

	def test_authenticated_user_can_add_once_and_remove(self):
		self.client.force_login(self.user)

		add_url = reverse('add_to_wishlist', args=[self.product.id])
		first_add = self.client.post(add_url)
		duplicate_add = self.client.post(add_url)

		self.assertEqual(first_add.status_code, 302)
		self.assertEqual(duplicate_add.status_code, 302)
		self.assertEqual(Wishlist.objects.filter(user=self.user, product=self.product).count(), 1)

		detail_response = self.client.get(reverse('wishlist_detail'))
		self.assertContains(detail_response, self.product.name)

		list_response = self.client.get(reverse('product_list'))
		product_detail_response = self.client.get(reverse('product_detail', args=[self.product.slug]))
		self.assertContains(list_response, 'Remove from wishlist')
		self.assertContains(product_detail_response, 'Remove from Wishlist')

		remove_response = self.client.post(reverse('remove_from_wishlist', args=[self.product.id]))

		self.assertEqual(remove_response.status_code, 302)
		self.assertFalse(Wishlist.objects.filter(user=self.user, product=self.product).exists())

	def test_inactive_product_cannot_be_added(self):
		self.client.force_login(self.user)

		response = self.client.post(reverse('add_to_wishlist', args=[self.inactive_product.id]))

		self.assertEqual(response.status_code, 404)
		self.assertFalse(Wishlist.objects.filter(product=self.inactive_product).exists())

	def test_wishlist_item_can_be_added_to_cart_and_persists_after_relogin(self):
		self.client.force_login(self.user)
		self.client.post(reverse('add_to_wishlist', args=[self.product.id]))

		cart_response = self.client.post(reverse('add_to_cart', args=[self.product.id]))

		self.assertEqual(cart_response.status_code, 302)
		self.assertEqual(self.client.session['cart'][str(self.product.id)], 1)

		self.client.logout()
		self.client.force_login(self.user)

		wishlist_response = self.client.get(reverse('wishlist_detail'))
		self.assertContains(wishlist_response, self.product.name)

# Create your tests here.
