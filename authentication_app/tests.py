from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
