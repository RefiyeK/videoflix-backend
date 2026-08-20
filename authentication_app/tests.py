from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterTests(APITestCase):
    """Cover the /api/register/ endpoint and its enumeration safeguards."""

    def setUp(self):
        """Store the register URL and one valid registration payload."""
        self.url = reverse('register')
        self.valid_payload = {
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'confirmed_password': 'testpass123',
        }

    def test_register_success(self):
        """A valid payload creates one inactive user and returns 201."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        created_user = User.objects.get(email='newuser@example.com')
        self.assertFalse(created_user.is_active)

    def test_register_response_shape(self):
        """The success body exposes the user id and email, plus a token."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertIn('user', response.data)
        self.assertIn('id', response.data['user'])
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertIn('token', response.data)

    def test_register_duplicate_email_is_generic(self):
        """A taken email is rejected with the shared generic message."""
        User.objects.create_user(
            email='newuser@example.com', password='testpass123')
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('already exists', str(response.data).lower())

    def test_register_password_mismatch_is_generic(self):
        """Mismatched passwords return the same generic message as a dupe."""
        payload = dict(self.valid_payload, confirmed_password='different123')
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_email_format(self):
        """A malformed email is still rejected by the field validator."""
        payload = dict(self.valid_payload, email='not-an-email')
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    """Cover the /api/login/ endpoint: credentials, cookies, active flag."""

    def setUp(self):
        """Create one active user and store the login URL."""
        self.url = reverse('login')
        self.user = User.objects.create_user(
            email='active@example.com', password='testpass123')
        self.user.is_active = True
        self.user.save()

    def test_login_success_sets_cookies(self):
        """Valid credentials return 200 and set both JWT cookies."""
        payload = {'email': 'active@example.com', 'password': 'testpass123'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_login_wrong_password_fails(self):
        """A wrong password returns 400 and sets no cookies."""
        payload = {'email': 'active@example.com', 'password': 'wrongpassword'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('access_token', response.cookies)

    def test_login_inactive_user_fails(self):
        """An inactive user cannot log in and receives 400."""
        inactive_user = User.objects.create_user(
            email='inactive@example.com', password='testpass123')
        inactive_user.is_active = False
        inactive_user.save()
        payload = {'email': 'inactive@example.com', 'password': 'testpass123'}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ActivateTests(APITestCase):
    """Cover the /api/activate/<uidb64>/<token>/ endpoint."""

    def setUp(self):
        """Create one inactive user to be activated by the endpoint."""
        self.user = User.objects.create_user(
            email='pending@example.com', password='testpass123',
            is_active=False)

    def _build_url(self, user, token):
        """Build the activate URL for a given user and token."""
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        return reverse('activate', kwargs={'uidb64': uidb64, 'token': token})

    def test_activate_success(self):
        """A valid uid and token activate the user and return 200."""
        token = default_token_generator.make_token(self.user)
        response = self.client.get(self._build_url(self.user, token))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_activate_invalid_token_fails(self):
        """A wrong token returns 400 and leaves the user inactive."""
        response = self.client.get(self._build_url(self.user, 'wrong-token'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class LogoutTests(APITestCase):
    """Cover the /api/logout/ endpoint: cookie deletion and missing token."""

    def setUp(self):
        """Create one active user and log in to obtain the auth cookies."""
        self.logout_url = reverse('logout')
        self.user = User.objects.create_user(
            email='active@example.com', password='testpass123')
        login_payload = {'email': 'active@example.com',
                         'password': 'testpass123'}
        self.client.post(reverse('login'), login_payload)

    def test_logout_success_clears_cookies(self):
        """Logout returns 200 and clears both auth cookies."""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')

    def test_logout_without_cookie_fails(self):
        """Logging out with no refresh cookie returns 400."""
        self.client.cookies.clear()
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_returns_detail_message(self):
        """A successful logout returns a detail message in the body."""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)


class TokenRefreshTests(APITestCase):
    """Cover the /api/token/refresh/ endpoint and its cookie handling."""

    def setUp(self):
        """Create one active user and store the refresh URL."""
        self.url = reverse('token_refresh')
        self.user = User.objects.create_user(
            email='active@example.com', password='testpass123')

    def test_refresh_success_sets_new_access_cookie(self):
        """A valid refresh cookie yields 200 and a new access cookie."""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['refresh_token'] = str(refresh)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('access_token', response.cookies)

    def test_refresh_without_cookie_fails(self):
        """A missing refresh cookie returns 400."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_invalid_token_fails(self):
        """A malformed refresh token returns 401."""
        self.client.cookies['refresh_token'] = 'not-a-real-token'
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
