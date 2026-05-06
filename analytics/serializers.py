from rest_framework import serializers
from finance.models import BudgetCategoryLimit, Transaction, Category

class BudgetAlertSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()
    alert_message = serializers.SerializerMethodField()

    class Meta:
        model = BudgetCategoryLimit
        fields = ['category_name', 'limit', 'spent', 'progress_percentage', 'status_color', 'alert_message']

    def get_progress_percentage(self, obj):
        if obj.limit > 0:
            return (obj.spent / obj.limit) * 100
        return 0

    def get_status_color(self, obj):
        percentage = self.get_progress_percentage(obj)
        if percentage >= 100:
            return "red"
        elif percentage >= 90:
            return "orange"
        return "green"

    def get_alert_message(self, obj):
        percentage = self.get_progress_percentage(obj)
        if percentage >= 100:
            diff = obj.spent - obj.limit
            return f"Budget Exceeded — {obj.category.name}! You've exceeded your ${obj.limit} budget by ${diff}."
        elif percentage >= 90:
            return f"Budget Alert — {obj.category.name}: You've used {percentage:.1f}% of your budget."
        return None

class TransactionReportSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Transaction
        fields = ['id', 'date', 'amount', 'type', 'category_name', 'description']

class CategorySpendingSerializer(serializers.Serializer):
    category = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    percentage = serializers.FloatField()


class DashboardSummarySerializer(serializers.Serializer):
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)

    recent_transactions = serializers.SerializerMethodField()

    budget_warnings = serializers.SerializerMethodField()

    def get_recent_transactions(self, obj):
        txs = Transaction.objects.filter(user=obj['user']).order_by('-date')[:5]
        from finance.serializers import TransactionSerializer
        return TransactionSerializer(txs, many=True).data

    def get_budget_warnings(self, obj):
        warnings = BudgetCategoryLimit.objects.filter(
            budget__user=obj['user'],
            spent__gte=0.9 * serializers.F('limit')
        )
        return [f"Warning: {w.category.name} is near its limit!" for w in warnings]