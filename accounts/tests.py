from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class AuthViewSetTest(APITestCase):
    """Tests for user registration, login, logout, and profile management."""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
        }

    def test_user_registration_success(self):
        """A new user can register with valid data."""
        response = self.client.post('/auth/', self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'], self.user_data['email'])
        self.assertNotIn('password', response.data)

    def test_user_registration_duplicate_email(self):
        """Registration fails when the email is already taken."""
        User.objects.create_user(**self.user_data)
        response = self.client.post('/auth/', self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_missing_email(self):
        """Registration fails when email is not provided."""
        data = {k: v for k, v in self.user_data.items() if k != 'email'}
        response = self.client.post('/auth/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        """A registered user can log in with correct credentials."""
        User.objects.create_user(**self.user_data)
        response = self.client.post('/auth/login/', {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])

    def test_user_login_wrong_password(self):
        """Login fails when the password is incorrect."""
        User.objects.create_user(**self.user_data)
        response = self.client.post('/auth/login/', {
            'email': self.user_data['email'],
            'password': 'wrongpassword',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_login_unknown_email(self):
        """Login fails when the email does not exist."""
        response = self.client.post('/auth/login/', {
            'email': 'nobody@example.com',
            'password': 'whatever',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile(self):
        """An authenticated user can retrieve their own profile."""
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        response = self.client.get('/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])
        self.assertNotIn('password', response.data)

    def test_get_profile_unauthenticated(self):
        """Unauthenticated requests to /auth/me/ are rejected."""
        response = self.client.get('/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_profile(self):
        """An authenticated user can update their first name and currency."""
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        response = self.client.patch('/auth/update_profile/', {
            'first_name': 'Updated',
            'currency': 'USD',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['currency'], 'USD')

    def test_logout(self):
        """An authenticated user can log out successfully."""
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        response = self.client.post('/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_logout_unauthenticated(self):
        """Unauthenticated requests to /auth/logout/ are rejected."""
        response = self.client.post('/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
