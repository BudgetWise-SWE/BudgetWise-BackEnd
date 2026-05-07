"""
Services for the finance application.

Contains the business logic for processing transactions, managing budgets,
and generating reports. This layer abstracts complex logic away from
views and models to maintain clean architecture.
"""
from django.db.models import Sum
from .models import Transaction, Budget, BudgetCategoryLimit


class BudgetService:
    """
    Service for linking expense transactions to budgets and updating spending totals.
    
    Handles the side effects of transaction creation on budget limits.
    """

    def get_budget_for_transaction(self, transaction):
        """
        Return the budget for the same month/year as the transaction, if one exists.
        
        Args:
            transaction (Transaction): The transaction instance.
            
        Returns:
            Budget: The matching budget instance or None.
        """
        return Budget.objects.filter(
            user=transaction.user,
            month=transaction.date.month,
            year=transaction.date.year,
        ).first()

    def process_expense(self, transaction):
        """
        Update the spent amount on the relevant budget category limit.
        
        Also triggers a recalculation of the overall budget status.
        
        Args:
            transaction (Transaction): The expense transaction being processed.
        """
        budget = self.get_budget_for_transaction(transaction)
        if not budget:
            return
        if transaction.category is not None:
            limit = BudgetCategoryLimit.objects.filter(
                budget=budget,
                category=transaction.category,
            ).first()
            if limit:
                limit.spent += transaction.amount
                limit.save(update_fields=['spent'])
                limit.update_status()
        budget.update_status()


class TransactionService:
    """
    Service for creating transactions and triggering post-creation side effects.
    
    Acts as the entry point for transaction creation logic.
    """

    def create_transaction(self, user, validated_data):
        """
        Create a transaction and process it against the budget if it's an expense.
        
        Args:
            user (User): The user creating the transaction.
            validated_data (dict): Validated input data from the serializer.
            
        Returns:
            Transaction: The newly created transaction.
        """
        validated_data['user'] = user
        transaction = Transaction.objects.create(**validated_data)
        if transaction.type == Transaction.TYPE_EXPENSE:
            BudgetService().process_expense(transaction)
        return transaction


class ReportService:
    """
    Service for generating financial reports aggregated by period or category.
    """

    def _period_queryset(self, user, month, year):
        """
        Return a queryset of the user's transactions, optionally filtered to a month/year.
        
        Args:
            user (User): The user whose data to fetch.
            month (int, optional): The month filter.
            year (int, optional): The year filter.
            
        Returns:
            QuerySet: Transaction queryset.
        """
        queryset = Transaction.objects.filter(user=user)
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        return queryset

    def monthly_summary(self, user, month=None, year=None):
        """
        Return total income, total expense, and net balance for the given period.
        
        Args:
            user (User): The user whose summary to generate.
            month (int, optional): Month filter.
            year (int, optional): Year filter.
            
        Returns:
            dict: Summary data containing 'income', 'expense', and 'balance'.
        """
        queryset = self._period_queryset(user, month, year)
        total_income = queryset.filter(
            type=Transaction.TYPE_INCOME
        ).aggregate(total=Sum('amount'))['total'] or 0
        total_expense = queryset.filter(
            type=Transaction.TYPE_EXPENSE
        ).aggregate(total=Sum('amount'))['total'] or 0
        return {
            'income': total_income,
            'expense': total_expense,
            'balance': total_income - total_expense,
        }

    def category_summary(self, user, month=None, year=None):
        """
        Return spending totals grouped by category for the given period.
        
        Args:
            user (User): The user whose summary to generate.
            month (int, optional): Month filter.
            year (int, optional): Year filter.
            
        Returns:
            list: List of dictionaries with 'category_id', 'category_name', and 'total'.
        """
        queryset = self._period_queryset(user, month, year).filter(category__isnull=False)
        data = (
            queryset
            .values('category__id', 'category__name')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        return [
            {
                'category_id': item['category__id'],
                'category_name': item['category__name'],
                'total': item['total'],
            }
            for item in data
        ]
