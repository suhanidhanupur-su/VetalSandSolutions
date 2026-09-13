from django.test import TestCase
from django.urls import reverse


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
