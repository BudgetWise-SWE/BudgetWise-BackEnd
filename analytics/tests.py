from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from finance.models import Category, Transaction, Budget, BudgetCategoryLimit
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class AnalyticsAPITest(APITestCase):
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

        # Create some test transactions
        Transaction.objects.create(
            user=self.user,
            type='expense',
            category=self.category,
            amount=Decimal('100.00'),
            date=timezone.now().date(),
            description='Test expense'
        )

    def test_budget_alerts(self):
        budget = Budget.objects.create(
            user=self.user,
            name='Test Budget',
            month=timezone.now().month,
            year=timezone.now().year,
            total_limit=Decimal('1000.00')
        )

        BudgetCategoryLimit.objects.create(
            budget=budget,
            category=self.category,
            limit=Decimal('200.00'),
            spent=Decimal('150.00')
        )

        response = self.client.get('/analytics/budget-alert/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_dashboard_summary(self):
        response = self.client.get('/analytics/dashboard-summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_balance', response.data)
        self.assertIn('monthly_income', response.data)
        self.assertIn('monthly_expenses', response.data)
        self.assertIn('recent_transactions', response.data)
        self.assertIn('budget_warnings', response.data)