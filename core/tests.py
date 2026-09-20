from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from products.models import Category, Product

from .models import GalleryImage


class CorePageViewsTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vetal Sand Solutions')
        self.assertContains(response, 'Request a Quote')
        self.assertContains(response, 'Home')

    def test_about_page_loads(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'About Vetal Sand Solutions')
        self.assertContains(response, 'Vetal Sand Solutions')
        self.assertContains(response, 'About')
        self.assertContains(response, 'Premium quality silica sand solutions for demanding industrial applications.')

    def test_industries_page_loads(self):
        response = self.client.get(reverse('industries'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Industries We Serve')
        self.assertContains(response, 'Foundries')
        self.assertContains(response, 'Castings')
        self.assertContains(response, 'Glass Manufacturing')

    def test_portfolio_page_loads(self):
        response = self.client.get(reverse('portfolio'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Company Profile')
        self.assertContains(response, 'What We Do')
        self.assertContains(response, 'Our Approach')
        self.assertContains(response, 'Quality')
        self.assertContains(response, 'Consistency')
        self.assertContains(response, 'Reliability')
        self.assertContains(response, 'Industries We Serve')
        self.assertContains(response, '16/30')
        self.assertContains(response, '24/40')
        self.assertContains(response, '45/50')
        self.assertContains(response, '50/60')
        self.assertContains(response, '60/70')

    def test_gallery_page_loads(self):
        response = self.client.get(reverse('gallery'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gallery')
        self.assertContains(response, 'Product and materials overview.')
        self.assertContains(response, 'Gallery images coming soon.')
        self.assertContains(response, 'Request a Quote')

    def test_gallery_page_shows_active_images_in_display_order(self):
        later_image = GalleryImage.objects.create(title='Second image', display_order=2)
        earlier_image = GalleryImage.objects.create(title='First image', display_order=1)
        GalleryImage.objects.create(title='Hidden image', is_active=False)

        response = self.client.get(reverse('gallery'))

        self.assertContains(response, earlier_image.title)
        self.assertContains(response, later_image.title)
        self.assertNotContains(response, 'Hidden image')
        self.assertLess(
            response.content.index(earlier_image.title.encode()),
            response.content.index(later_image.title.encode()),
        )

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='no-reply@example.com',
        COMPANY_NOTIFICATION_EMAIL='company@example.com',
    )
    def test_contact_submission_sends_customer_and_company_notifications(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Contact Customer',
            'email': 'customer@example.com',
            'message': 'Please contact me.',
        })

        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            {message.to[0] for message in mail.outbox},
            {'customer@example.com', 'company@example.com'},
        )

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
        EMAIL_HOST='',
        EMAIL_HOST_USER='',
        EMAIL_HOST_PASSWORD='',
        DEFAULT_FROM_EMAIL='',
        COMPANY_NOTIFICATION_EMAIL='company@example.com',
    )
    def test_contact_submission_does_not_crash_without_smtp(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Contact Customer',
            'email': 'customer@example.com',
            'message': 'Please contact me.',
        })

        self.assertRedirects(response, reverse('contact'))
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='no-reply@example.com',
        COMPANY_NOTIFICATION_EMAIL='company@example.com',
    )
    def test_quote_submission_sends_customer_and_company_notifications(self):
        category = Category.objects.create(name='Industrial', slug='industrial')
        product = Product.objects.create(category=category, name='Foundry Sand', slug='foundry-sand')

        response = self.client.post(reverse('quote'), {
            'name': 'Quote Customer',
            'email': 'customer@example.com',
            'product': product.id,
            'grade': '16/30',
            'quantity': '10 tons',
            'application': 'Foundry',
            'location': 'Pune',
            'message': 'Please share pricing.',
        })

        self.assertRedirects(response, reverse('quote'))
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            {message.to[0] for message in mail.outbox},
            {'customer@example.com', 'company@example.com'},
        )
