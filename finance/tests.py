from django.test import TestCase

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Transaction, Budget, BudgetCategoryLimit, SavingsGoal
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class FinanceAPITest(APITestCase):
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

    def test_category_crud(self):
        # Create
        category_data = {
            'name': 'Transport',
            'type': 'expense'
        }
        response = self.client.post('/finance/categories/', category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Read
        response = self.client.get('/finance/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

        # Update
        category_id = response.data[0]['id']
        update_data = {'name': 'Updated Transport'}
        response = self.client.patch(f'/finance/categories/{category_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f'/finance/categories/{category_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_transaction_crud(self):
        # Create
        transaction_data = {
            'type': 'expense',
            'category': self.category.id,
            'amount': '50.00',
            'date': '2024-01-01',
            'description': 'Lunch'
        }
        response = self.client.post('/finance/transactions/', transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Read
        response = self.client.get('/finance/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

        # Summary
        response = self.client.get('/finance/transactions/summary/?month=1&year=2024')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('income', response.data)
        self.assertIn('expense', response.data)
        self.assertIn('balance', response.data)

        # By category
        response = self.client.get('/finance/transactions/by_category/?month=1&year=2024')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_budget_crud(self):
        # Create
        budget_data = {
            'name': 'January Budget',
            'month': 1,
            'year': 2024,
            'total_limit': '1000.00'
        }
        response = self.client.post('/finance/budgets/', budget_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Read
        response = self.client.get('/finance/budgets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_budget_category_limit_crud(self):
        budget = Budget.objects.create(
            user=self.user,
            name='Test Budget',
            month=1,
            year=2024,
            total_limit=Decimal('1000.00')
        )

        # Create
        limit_data = {
            'budget': budget.id,
            'category': self.category.id,
            'limit': '200.00'
        }
        response = self.client.post('/finance/budget-category-limits/', limit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Read
        response = self.client.get('/finance/budget-category-limits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_savings_goal_crud(self):
        # Create
        goal_data = {
            'name': 'Vacation Fund',
            'target_amount': '5000.00',
            'deadline': '2024-12-31'
        }
        response = self.client.post('/finance/savings-goals/', goal_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Read
        response = self.client.get('/finance/savings-goals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_reports(self):
        # Monthly report
        response = self.client.get('/finance/reports/monthly/?month=1&year=2024')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Category report
        response = self.client.get('/finance/reports/by_category/?month=1&year=2024')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
