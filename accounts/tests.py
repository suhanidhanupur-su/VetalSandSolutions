from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class AuthenticationUrlTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.password = 'Strong-test-password-123!'
        self.user = self.user_model.objects.create_user(
            username='existing-user',
            email='existing@example.com',
            password=self.password,
        )

    def test_register_page_is_available(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'Confirm Password')

    def test_login_page_is_available(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_account_page_requires_login(self):
        response = self.client.get(reverse('account'))
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("account")}',
        )

    def test_registration_hashes_password_and_logs_user_in(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'new-user',
                'email': 'new@example.com',
                'password1': 'Another-strong-password-123!',
                'password2': 'Another-strong-password-123!',
            },
        )

        self.assertRedirects(response, reverse('account'))
        user = self.user_model.objects.get(username='new-user')
        self.assertNotEqual(user.password, 'Another-strong-password-123!')
        self.assertTrue(user.check_password('Another-strong-password-123!'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_duplicate_username_is_rejected_without_creating_user(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': self.user.username,
                'email': 'duplicate@example.com',
                'password1': 'Another-strong-password-123!',
                'password2': 'Another-strong-password-123!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that username already exists')
        self.assertEqual(self.user_model.objects.filter(username=self.user.username).count(), 1)

    def test_invalid_password_shows_error_without_authenticating(self):
        response = self.client.post(
            reverse('login'),
            {'username': self.user.username, 'password': 'wrong-password'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_honors_safe_next_url(self):
        next_url = reverse('wishlist_detail')
        response = self.client.post(
            f'{reverse("login")}?next={next_url}',
            {'username': self.user.username, 'password': self.password},
        )

        self.assertRedirects(response, next_url)
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_login_rejects_external_next_url(self):
        response = self.client.post(
            f'{reverse("login")}?next=https://example.com/account/',
            {'username': self.user.username, 'password': self.password},
        )

        self.assertRedirects(response, reverse('account'))

    def test_logout_requires_post_and_clears_authentication(self):
        self.client.force_login(self.user)
        get_response = self.client.get(reverse('logout'))
        self.assertEqual(get_response.status_code, 405)

        post_response = self.client.post(reverse('logout'))
        self.assertRedirects(post_response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_navbar_switches_between_logged_out_and_logged_in_states(self):
        logged_out_response = self.client.get(reverse('home'))
        self.assertContains(logged_out_response, 'Login')
        self.assertContains(logged_out_response, 'Register')
        self.assertNotContains(logged_out_response, '>Account<')

        self.client.force_login(self.user)
        logged_in_response = self.client.get(reverse('home'))
        self.assertContains(logged_in_response, '>Account<')
        self.assertContains(logged_in_response, '>Logout<')
        self.assertNotContains(logged_in_response, '>Register<')

    def test_profile_page_is_protected_and_is_not_account_dashboard(self):
        response = self.client.get(reverse('edit_profile'))

        self.assertRedirects(response, f'{reverse("login")}?next={reverse("edit_profile")}')

        self.client.force_login(self.user)
        profile_response = self.client.get(reverse('edit_profile'))
        account_response = self.client.get(reverse('account'))

        self.assertEqual(profile_response.status_code, 200)
        self.assertContains(profile_response, 'My Profile')
        self.assertContains(profile_response, 'Full name')
        self.assertContains(profile_response, 'Phone number')
        self.assertContains(profile_response, 'Save Changes')
        self.assertContains(account_response, 'My Account')

    def test_profile_update_only_changes_logged_in_users_profile(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('edit_profile'),
            {'full_name': 'Updated Customer', 'phone_number': '+91 9876543210'},
        )

        self.assertRedirects(response, reverse('edit_profile'))
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, 'Updated Customer')
        self.assertEqual(profile.phone_number, '+91 9876543210')

    def test_account_and_navbar_profile_links_use_edit_profile(self):
        self.client.force_login(self.user)

        account_response = self.client.get(reverse('account'))
        home_response = self.client.get(reverse('home'))

        self.assertContains(account_response, reverse('edit_profile'))
        self.assertContains(home_response, reverse('edit_profile'))
        self.assertNotContains(home_response, 'href="/account/">My Profile')
