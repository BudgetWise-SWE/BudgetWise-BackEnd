from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from finance.models import Category, Budget, BudgetCategoryLimit, SavingsGoal
from decimal import Decimal
from django.utils import timezone

User = get_user_model()


class PlanningAPITest(APITestCase):
    """Tests for planning endpoints: budget limit creation and savings goal management."""

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

    def test_budget_limit_creation(self):
        """A user can create a budget limit for the current month."""
        response = self.client.post('/planning/budget-limit/', {
            'category': self.category.id,
            'limit': '300.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)

    def test_budget_limit_creates_budget_automatically(self):
        """Creating a budget limit automatically creates the month's budget if missing."""
        now = timezone.now()
        self.assertFalse(
            Budget.objects.filter(
                user=self.user, month=now.month, year=now.year
            ).exists()
        )
        self.client.post('/planning/budget-limit/', {
            'category': self.category.id,
            'limit': '300.00',
        }, format='json')
        self.assertTrue(
            Budget.objects.filter(
                user=self.user, month=now.month, year=now.year
            ).exists()
        )

    def test_duplicate_budget_limit_rejected(self):
        """Creating a second limit for the same category in the same month is rejected."""
        now = timezone.now()
        budget = Budget.objects.create(
            user=self.user,
            name='Budget',
            month=now.month,
            year=now.year,
            total_limit=Decimal('1000.00'),
        )
        BudgetCategoryLimit.objects.create(
            budget=budget, category=self.category, limit=Decimal('200.00')
        )
        response = self.client.post('/planning/budget-limit/', {
            'category': self.category.id,
            'limit': '300.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_limit_rejected(self):
        """A budget limit with a zero or negative amount is rejected."""
        response = self.client.post('/planning/budget-limit/', {
            'category': self.category.id,
            'limit': '-100.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_budget_limit_unauthenticated(self):
        """Unauthenticated requests to budget-limit are rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/planning/budget-limit/', {
            'category': self.category.id,
            'limit': '200.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_savings_goal_create(self):
        """A user can create a savings goal."""
        response = self.client.post('/planning/savings-goal/', {
            'name': 'Emergency Fund',
            'target_amount': '10000.00',
            'deadline': '2026-12-31',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertIn('monthly_savings_needed', response.data)
        self.assertIn('progress_percentage', response.data)

    def test_savings_goal_list(self):
        """A user can list their savings goals."""
        SavingsGoal.objects.create(
            user=self.user, name='Car', target_amount=Decimal('20000.00')
        )
        response = self.client.get('/planning/savings-goal/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertIn('monthly_savings_needed', response.data[0])
        self.assertIn('progress_percentage', response.data[0])

    def test_savings_goal_progress_zero_initially(self):
        """A newly created savings goal has 0% progress."""
        response = self.client.post('/planning/savings-goal/', {
            'name': 'Fund',
            'target_amount': '5000.00',
            'deadline': '2027-01-01',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['progress_percentage'], 0)

    def test_savings_goal_unauthenticated(self):
        """Unauthenticated requests to savings-goal are rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/planning/savings-goal/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
