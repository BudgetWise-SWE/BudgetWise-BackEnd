from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from finance.models import Category, Transaction, Budget, BudgetCategoryLimit
from decimal import Decimal
from django.utils import timezone

User = get_user_model()


class AnalyticsAPITest(APITestCase):
    """Tests for analytics endpoints: budget alerts, reports, and dashboard summary."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(
            name='Food', type='expense', user=self.user
        )

        Transaction.objects.create(
            user=self.user,
            type='expense',
            category=self.category,
            amount=Decimal('100.00'),
            date=timezone.now().date(),
            description='Test expense',
        )

        Transaction.objects.create(
            user=self.user,
            type='income',
            amount=Decimal('2000.00'),
            date=timezone.now().date(),
            description='Salary',
            source='Employer',
        )

    def test_budget_alerts_authenticated(self):
        """Budget alert endpoint returns a list for authenticated users."""
        budget = Budget.objects.create(
            user=self.user,
            name='Test Budget',
            month=timezone.now().month,
            year=timezone.now().year,
            total_limit=Decimal('1000.00'),
        )
        BudgetCategoryLimit.objects.create(
            budget=budget,
            category=self.category,
            limit=Decimal('200.00'),
            spent=Decimal('150.00'),
        )
        response = self.client.get('/analytics/budget-alert/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertIn('category_name', response.data[0])
        self.assertIn('progress_percentage', response.data[0])
        self.assertIn('status_color', response.data[0])

    def test_budget_alerts_unauthenticated(self):
        """Unauthenticated requests to budget-alert are rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/analytics/budget-alert/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_summary(self):
        """Dashboard summary returns all required fields."""
        response = self.client.get('/analytics/dashboard-summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_balance', response.data)
        self.assertIn('monthly_income', response.data)
        self.assertIn('monthly_expenses', response.data)
        self.assertIn('recent_transactions', response.data)
        self.assertIn('budget_warnings', response.data)

    def test_dashboard_balance_is_correct(self):
        """Dashboard total_balance equals income minus expenses."""
        response = self.client.get('/analytics/dashboard-summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_balance = Decimal('2000.00') - Decimal('100.00')
        self.assertEqual(Decimal(str(response.data['total_balance'])), expected_balance)

    def test_dashboard_unauthenticated(self):
        """Unauthenticated requests to dashboard-summary are rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/analytics/dashboard-summary/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reports_analytics_with_data(self):
        """Reports analytics returns pie chart and bar chart when transactions exist."""
        today = timezone.now().date()
        response = self.client.get(
            f'/analytics/reports/?start_date={today.replace(day=1)}&end_date={today}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pie_chart', response.data)
        self.assertIn('bar_chart', response.data)
        self.assertIn('insight', response.data)

    def test_reports_analytics_empty_period(self):
        """Reports analytics returns an informative message when no transactions exist."""
        response = self.client.get('/analytics/reports/?start_date=2000-01-01&end_date=2000-01-31')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_reports_analytics_unauthenticated(self):
        """Unauthenticated requests to analytics reports are rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/analytics/reports/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)