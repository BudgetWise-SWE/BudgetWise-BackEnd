from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Notification

User = get_user_model()

class NotificationsAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_notification_crud(self):
        notification_data = {
            'type': 'budget_alert',
            'title': 'Budget Alert',
            'message': 'You are close to your budget limit'
        }
        response = self.client.post('/notifications/notifications/', notification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get('/notifications/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

        notification_id = response.data[0]['id']

        response = self.client.post(f'/notifications/notifications/{notification_id}/mark_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post('/notifications/notifications/mark_all_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class AuthAPITest(APITestCase):
    def test_registration_and_login(self):
        register_data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'securepassword123'
        }
        response = self.client.post('/auth/', register_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        login_data = {
            'email': 'newuser@example.com',
            'password': 'securepassword123'
        }
        response = self.client.post('/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)

    def test_me_endpoint(self):
        user = User.objects.create_user(email='me@example.com', password='pass')
        self.client.force_authenticate(user=user)
        response = self.client.get('/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'me@example.com')

class FinanceAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='finance@example.com', password='pass')
        self.client.force_authenticate(user=self.user)

    def test_transaction_summary(self):
        response = self.client.get('/finance/transactions/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)