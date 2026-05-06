from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Notification

User = get_user_model()


class NotificationsAPITest(APITestCase):
    """Tests for the /notifications/notifications/ endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)

    def _create_notification(self, **kwargs):
        """Helper to create a notification via the API."""
        data = {
            'type': 'budget_alert',
            'title': 'Budget Alert',
            'message': 'You are close to your budget limit',
        }
        data.update(kwargs)
        return self.client.post('/notifications/notifications/', data, format='json')

    def test_create_notification(self):
        """A user can create a notification."""
        response = self._create_notification()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['type'], 'budget_alert')

    def test_list_notifications(self):
        """A user can list their notifications."""
        self._create_notification()
        response = self.client.get('/notifications/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_mark_single_notification_read(self):
        """A user can mark a single notification as read."""
        create_response = self._create_notification()
        notification_id = create_response.data['id']
        response = self.client.post(f'/notifications/notifications/{notification_id}/mark_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification = Notification.objects.get(id=notification_id)
        self.assertTrue(notification.is_read)

    def test_mark_read_is_idempotent(self):
        """Marking an already-read notification as read does not cause an error."""
        create_response = self._create_notification()
        notification_id = create_response.data['id']
        self.client.post(f'/notifications/notifications/{notification_id}/mark_read/')
        response = self.client.post(f'/notifications/notifications/{notification_id}/mark_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_mark_all_notifications_read(self):
        """A user can mark all their notifications as read at once."""
        self._create_notification(title='First')
        self._create_notification(title='Second')
        response = self.client.post('/notifications/notifications/mark_all_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unread = Notification.objects.filter(user=self.user, is_read=False).count()
        self.assertEqual(unread, 0)

    def test_user_cannot_see_other_user_notifications(self):
        """A user cannot access notifications belonging to another user."""
        other_user = User.objects.create_user(email='other@example.com', password='pass')
        Notification.objects.create(
            user=other_user,
            type='system',
            title='Private',
            message='Not for you',
        )
        response = self.client.get('/notifications/notifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_unauthenticated_access_rejected(self):
        """Unauthenticated requests to notifications are rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/notifications/notifications/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_notification(self):
        """A user can delete their own notification."""
        create_response = self._create_notification()
        notification_id = create_response.data['id']
        response = self.client.delete(f'/notifications/notifications/{notification_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)