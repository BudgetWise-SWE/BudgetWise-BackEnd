from rest_framework import serializers
from decimal import Decimal
from finance.models import BudgetCategoryLimit, Transaction, Category


class BudgetAlertSerializer(serializers.ModelSerializer):
    """Serializer for budget category limit alerts with computed progress and status color."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()
    alert_message = serializers.SerializerMethodField()

    class Meta:
        model = BudgetCategoryLimit
        fields = ['category_name', 'limit', 'spent', 'progress_percentage', 'status_color', 'alert_message']

    def get_progress_percentage(self, obj):
        """Return spending as a percentage of the limit."""
        if obj.limit > 0:
            return round((obj.spent / obj.limit) * 100, 2)
        return 0

    def get_status_color(self, obj):
        """Return a color string based on how close spending is to the limit."""
        percentage = self.get_progress_percentage(obj)
        if percentage >= 100:
            return 'red'
        elif percentage >= 90:
            return 'orange'
        return 'green'

    def get_alert_message(self, obj):
        """Return a human-readable alert message if the limit is near or exceeded."""
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
    """Serializer for transaction data in reports."""

    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Transaction
        fields = ['id', 'date', 'amount', 'type', 'category_name', 'description']


class CategorySpendingSerializer(serializers.Serializer):
    """Serializer for category-level spending breakdown used in analytics charts."""

    category = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    percentage = serializers.FloatField()


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for the dashboard home page summary."""

    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    recent_transactions = serializers.SerializerMethodField()
    budget_warnings = serializers.SerializerMethodField()

    def get_recent_transactions(self, obj):
        """Return the 5 most recent transactions for the user."""
        txs = Transaction.objects.filter(user=obj['user']).order_by('-date')[:5]
        from finance.serializers import TransactionSerializer
        return TransactionSerializer(txs, many=True).data

    def get_budget_warnings(self, obj):
        """Return warning strings for budget category limits that are at or near their limit."""
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