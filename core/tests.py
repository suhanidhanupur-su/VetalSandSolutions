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
