"""
Serializers for the analytics application.

Provides data structures for financial reports, budget alerts,
dashboard summaries, and categorical spending breakdowns.
"""
from rest_framework import serializers
from decimal import Decimal
from finance.models import BudgetCategoryLimit, Transaction, Category


class BudgetAlertSerializer(serializers.ModelSerializer):
    """
    Serializer for budget category limit alerts.
    
    Computes visual cues like progress percentage, status color (green/orange/red),
    and human-readable alert messages.
    """

    category_name = serializers.CharField(source='category.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()
    alert_message = serializers.SerializerMethodField()

    class Meta:
        """Metadata for BudgetAlertSerializer."""
        model = BudgetCategoryLimit
        fields = ['category_name', 'limit', 'spent', 'progress_percentage', 'status_color', 'alert_message']

    def get_progress_percentage(self, obj):
        """
        Calculate spending as a percentage of the limit.
        
        Args:
            obj (BudgetCategoryLimit): The limit instance.
            
        Returns:
            float: Percentage value rounded to 2 decimal places.
        """
        if obj.limit > 0:
            return round((obj.spent / obj.limit) * 100, 2)
        return 0

    def get_status_color(self, obj):
        """
        Determine the visual status color based on consumption.
        
        - 100%+ -> red
        - 90%-100% -> orange
        - <90% -> green
        
        Returns:
            str: Color code.
        """
        percentage = self.get_progress_percentage(obj)
        if percentage >= 100:
            return 'red'
        elif percentage >= 90:
            return 'orange'
        return 'green'

    def get_alert_message(self, obj):
        """
        Generate a human-readable notification message for the budget status.
        
        Returns:
            str: Warning message or None.
        """
        percentage = self.get_progress_percentage(obj)
        if percentage >= 100:
            diff = obj.spent - obj.limit
            return (
                f"Budget Exceeded — {obj.category.name}! "
                f"You've exceeded your {obj.limit} budget by {diff}."
            )
        elif percentage >= 90:
            return (
                f"Budget Alert — {obj.category.name}: "
                f"You've used {percentage:.1f}% of your budget."
            )
        return None


class TransactionReportSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for transaction data within analytical reports.
    """

    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        """Metadata for TransactionReportSerializer."""
        model = Transaction
        fields = ['id', 'date', 'amount', 'type', 'category_name', 'description']


class CategorySpendingSerializer(serializers.Serializer):
    """
    Data structure for category-level spending breakdown.
    
    Used primarily for pie charts and data visualization.
    """

    category = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    percentage = serializers.FloatField()


class DashboardSummarySerializer(serializers.Serializer):
    """
    Serializer for the main dashboard home page.
    
    Aggregates balance, monthly income/expenses, and lists recent transactions
    and budget warnings.
    """

    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    remaining = serializers.DecimalField(source='total_balance', max_digits=12, decimal_places=2)
    total_income = serializers.DecimalField(source='monthly_income', max_digits=12, decimal_places=2)
    total_expenses = serializers.SerializerMethodField()
    total_transactions = serializers.SerializerMethodField()
    num_of_trans = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()
    budget_warnings = serializers.SerializerMethodField()

    def get_total_expenses(self, obj):
        """
        Return negative expenses to match frontend expected summation.
        """
        return -obj['monthly_expenses']

    def get_num_of_trans(self, obj):
        """
        Alias for total_transactions as expected by dashboard.js IDs.
        """
        return self.get_total_transactions(obj)

    def get_total_transactions(self, obj):
        """
        Count the total number of transactions for the user.
        """
        return Transaction.objects.filter(user=obj['user']).count()

    def get_recent_transactions(self, obj):
        """
        Fetch the 5 most recent transactions for the user.
        
        Args:
            obj (dict): Context object containing 'user'.
            
        Returns:
            list: List of serialized transactions.
        """
        txs = Transaction.objects.filter(user=obj['user']).order_by('-date')[:5]
        from finance.serializers import TransactionSerializer
        return TransactionSerializer(txs, many=True).data

    def get_budget_warnings(self, obj):
        """
        Identify budgets that are at or near their limit.
        
        Returns:
            list: List of warning strings.
        """
        warnings = BudgetCategoryLimit.objects.filter(
            budget__user=obj['user'],
        ).select_related('category')
        result = []
        for w in warnings:
            if w.limit > 0 and w.spent >= w.limit * 1:
                result.append(f"Warning: {w.category.name} budget exceeded!")
            elif w.limit > 0 and w.spent >= w.limit * Decimal('0.9'):
                result.append(f"Warning: {w.category.name} is near its limit!")
        return result