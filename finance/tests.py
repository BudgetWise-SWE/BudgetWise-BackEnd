from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from finance.models import Category, Transaction, Budget, BudgetCategoryLimit, SavingsGoal
from decimal import Decimal
from django.utils import timezone

User = get_user_model()


class CategoryAPITest(APITestCase):
    """Tests for the /finance/categories/ endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)

    def test_create_category(self):
        """A user can create a custom category."""
        response = self.client.post('/finance/categories/', {
            'name': 'Transport',
            'type': 'expense',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Transport')
        self.assertFalse(response.data['is_predefined'])

    def test_list_categories(self):
        """A user can list their own and predefined categories."""
        Category.objects.create(name='Food', type='expense', user=self.user)
        Category.objects.create(name='Salary', type='income', is_predefined=True)
        response = self.client.get('/finance/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_update_category(self):
        """A user can update their own category."""
        cat = Category.objects.create(name='Food', type='expense', user=self.user)
        response = self.client.patch(f'/finance/categories/{cat.id}/', {
            'name': 'Groceries',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Groceries')

    def test_delete_category(self):
        """A user can delete their own category."""
        cat = Category.objects.create(name='Food', type='expense', user=self.user)
        response = self.client.delete(f'/finance/categories/{cat.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_unauthenticated_access(self):
        """Unauthenticated requests are rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/finance/categories/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TransactionAPITest(APITestCase):
    """Tests for the /finance/transactions/ endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)
        self.expense_category = Category.objects.create(
            name='Food', type='expense', user=self.user
        )
        self.income_category = Category.objects.create(
            name='Salary', type='income', user=self.user
        )

    def test_create_expense_transaction(self):
        """A user can create an expense transaction."""
        response = self.client.post('/finance/transactions/', {
            'type': 'expense',
            'category': self.expense_category.id,
            'amount': '50.00',
            'date': '2024-01-15',
            'description': 'Lunch',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['type'], 'expense')
        self.assertIn('category_name', response.data)

    def test_create_income_transaction(self):
        """A user can create an income transaction with a source."""
        response = self.client.post('/finance/transactions/', {
            'type': 'income',
            'category': self.income_category.id,
            'amount': '1500.00',
            'date': '2024-01-01',
            'description': 'Monthly salary',
            'source': 'Employer ABC',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_income_requires_source(self):
        """Creating an income transaction without a source fails."""
        response = self.client.post('/finance/transactions/', {
            'type': 'income',
            'amount': '1000.00',
            'date': '2024-01-01',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_amount_rejected(self):
        """Transactions with a zero or negative amount are rejected."""
        response = self.client.post('/finance/transactions/', {
            'type': 'expense',
            'amount': '-50.00',
            'date': '2024-01-01',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_category_type_mismatch_rejected(self):
        """An expense transaction assigned to an income category is rejected."""
        response = self.client.post('/finance/transactions/', {
            'type': 'expense',
            'category': self.income_category.id,
            'amount': '50.00',
            'date': '2024-01-01',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_transactions(self):
        """A user can list their transactions."""
        Transaction.objects.create(
            user=self.user, type='expense',
            category=self.expense_category, amount=Decimal('30.00'),
            date='2024-01-01',
        )
        response = self.client.get('/finance/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_filter_transactions_by_type(self):
        """The transaction list can be filtered by type."""
        Transaction.objects.create(
            user=self.user, type='expense', category=self.expense_category,
            amount=Decimal('30.00'), date='2024-01-01',
        )
        Transaction.objects.create(
            user=self.user, type='income', category=self.income_category,
            amount=Decimal('500.00'), date='2024-01-01', source='Job',
        )
        response = self.client.get('/finance/transactions/?type=expense')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(t['type'] == 'expense' for t in response.data))

    def test_filter_transactions_by_date_range(self):
        """The transaction list can be filtered by date range."""
        Transaction.objects.create(
            user=self.user, type='expense', category=self.expense_category,
            amount=Decimal('30.00'), date='2024-01-01',
        )
        Transaction.objects.create(
            user=self.user, type='expense', category=self.expense_category,
            amount=Decimal('50.00'), date='2024-03-01',
        )
        response = self.client.get('/finance/transactions/?date_from=2024-01-01&date_to=2024-01-31')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_transaction_summary(self):
        """The summary endpoint returns income, expense, and balance."""
        response = self.client.get('/finance/transactions/summary/?month=1&year=2024')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('income', response.data)
        self.assertIn('expense', response.data)
        self.assertIn('balance', response.data)

    def test_transaction_by_category(self):
        """The by_category endpoint aggregates spending per category."""
        Transaction.objects.create(
            user=self.user, type='expense', category=self.expense_category,
            amount=Decimal('100.00'), date='2024-01-05',
        )
        response = self.client.get('/finance/transactions/by_category/?month=1&year=2024')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_user_cannot_see_other_user_transactions(self):
        """A user cannot access another user's transactions."""
        other_user = User.objects.create_user(
            email='other@example.com', password='pass'
        )
        Transaction.objects.create(
            user=other_user, type='expense', category=self.expense_category,
            amount=Decimal('99.00'), date='2024-01-01',
        )
        response = self.client.get('/finance/transactions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class BudgetAPITest(APITestCase):
    """Tests for the /finance/budgets/ and /finance/budget-category-limits/ endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Food', type='expense', user=self.user)

    def test_create_budget(self):
        """A user can create a monthly budget."""
        response = self.client.post('/finance/budgets/', {
            'name': 'January Budget',
            'month': 1,
            'year': 2024,
            'total_limit': '1000.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('spent', response.data)
        self.assertIn('remaining', response.data)

    def test_budget_status_updates_after_expense(self):
        """Creating an expense updates the related budget status."""
        budget = Budget.objects.create(
            user=self.user, name='Jan', month=1, year=2024, total_limit=Decimal('100.00')
        )
        self.client.post('/finance/transactions/', {
            'type': 'expense',
            'category': self.category.id,
            'amount': '150.00',
            'date': '2024-01-15',
        }, format='json')
        budget.refresh_from_db()
        self.assertEqual(budget.status, 'exceeded')

    def test_create_budget_category_limit(self):
        """A user can create a category spending limit within a budget."""
        budget = Budget.objects.create(
            user=self.user, name='Jan', month=1, year=2024, total_limit=Decimal('1000.00')
        )
        response = self.client.post('/finance/budget-category-limits/', {
            'budget': budget.id,
            'category': self.category.id,
            'limit': '300.00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('category_name', response.data)
        self.assertIn('remaining', response.data)


class SavingsGoalAPITest(APITestCase):
    """Tests for the /finance/savings-goals/ endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)

    def test_create_savings_goal(self):
        """A user can create a savings goal."""
        response = self.client.post('/finance/savings-goals/', {
            'name': 'Vacation Fund',
            'target_amount': '5000.00',
            'deadline': '2025-12-31',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('progress', response.data)

    def test_list_savings_goals(self):
        """A user can list their savings goals."""
        SavingsGoal.objects.create(
            user=self.user, name='Car', target_amount=Decimal('20000.00')
        )
        response = self.client.get('/finance/savings-goals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_contribute_to_savings_goal(self):
        """A user can contribute funds to a savings goal."""
        goal = SavingsGoal.objects.create(
            user=self.user, name='Emergency Fund', target_amount=Decimal('10000.00')
        )
        response = self.client.post(
            f'/finance/savings-goals/{goal.id}/contribute/',
            {'amount': '500.00'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data['current_amount'])), Decimal('500.00'))

    def test_contribute_completes_goal(self):
        """Contributing the full target amount marks the goal as completed."""
        goal = SavingsGoal.objects.create(
            user=self.user, name='Laptop', target_amount=Decimal('1000.00')
        )
        self.client.post(
            f'/finance/savings-goals/{goal.id}/contribute/',
            {'amount': '1000.00'},
            format='json',
        )
        goal.refresh_from_db()
        self.assertTrue(goal.completed)

    def test_contribute_negative_amount_rejected(self):
        """Contributing a negative amount is rejected."""
        goal = SavingsGoal.objects.create(
            user=self.user, name='Fund', target_amount=Decimal('1000.00')
        )
        response = self.client.post(
            f'/finance/savings-goals/{goal.id}/contribute/',
            {'amount': '-100.00'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_contribute_missing_amount_rejected(self):
        """A contribution request without an amount field is rejected."""
        goal = SavingsGoal.objects.create(
            user=self.user, name='Fund', target_amount=Decimal('1000.00')
        )
        response = self.client.post(
            f'/finance/savings-goals/{goal.id}/contribute/',
            {},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReportAPITest(APITestCase):
    """Tests for the /finance/reports/ endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)

    def test_monthly_report(self):
        """The monthly report returns income, expense, and balance."""
        response = self.client.get('/finance/reports/monthly/?month=1&year=2024')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('income', response.data)
        self.assertIn('balance', response.data)

    def test_category_report(self):
        """The category report returns a list of category spending totals."""
        response = self.client.get('/finance/reports/by_category/?month=1&year=2024')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_report_unauthenticated(self):
        """Unauthenticated access to reports is rejected."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/finance/reports/monthly/?month=1&year=2024')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
