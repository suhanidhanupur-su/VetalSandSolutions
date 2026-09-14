from django.test import TestCase
from django.urls import reverse


class AuthenticationUrlTests(TestCase):
    def test_register_page_is_available(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_is_available(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_account_page_requires_login(self):
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 302)
