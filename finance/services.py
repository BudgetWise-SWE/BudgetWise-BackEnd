from django.db.models import Sum
from .models import Transaction, Budget, BudgetCategoryLimit


class BudgetService:
    """Service for linking expense transactions to budgets and updating spending totals."""

    def get_budget_for_transaction(self, transaction):
        """Return the budget for the same month/year as the transaction, if one exists."""
        return Budget.objects.filter(
            user=transaction.user,
            month=transaction.date.month,
            year=transaction.date.year,
        ).first()

    def process_expense(self, transaction):
        """
        Update the spent amount on the relevant budget category limit
        and recalculate the overall budget status.
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
    """Service for creating transactions and triggering post-creation side effects."""

    def create_transaction(self, user, validated_data):
        """Create a transaction and, if it is an expense, process it against the budget."""
        validated_data['user'] = user
        transaction = Transaction.objects.create(**validated_data)
        if transaction.type == Transaction.TYPE_EXPENSE:
            BudgetService().process_expense(transaction)
        return transaction


class ReportService:
    """Service for generating financial reports aggregated by period or category."""

    def _period_queryset(self, user, month, year):
        """Return a queryset of the user's transactions, optionally filtered to a month/year."""
        queryset = Transaction.objects.filter(user=user)
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        return queryset

    def monthly_summary(self, user, month=None, year=None):
        """Return total income, total expense, and net balance for the given period."""
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
        """Return spending totals grouped by category for the given period."""
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
