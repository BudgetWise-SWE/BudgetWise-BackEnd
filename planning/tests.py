from django.test import TestCase

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from finance.models import Category, Budget, BudgetCategoryLimit, SavingsGoal
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class PlanningAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(
            name='Food',
            type='expense',
            user=self.user
        )

    def test_budget_limit_creation(self):
        limit_data = {
            'category': self.category.id,
            'limit': '300.00'
        }
        response = self.client.post('/planning/budget-limit/', limit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)

    def test_savings_goal_crud(self):
        # Create
        goal_data = {
            'name': 'Emergency Fund',
            'target_amount': '10000.00',
            'deadline': '2025-12-31'
        }
        response = self.client.post('/planning/savings-goal/', goal_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

        # Read
        response = self.client.get('/planning/savings-goal/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertIn('monthly_savings_needed', response.data[0])
        self.assertIn('progress_percentage', response.data[0])
