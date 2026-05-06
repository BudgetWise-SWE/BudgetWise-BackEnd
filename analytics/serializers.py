from rest_framework import serializers
from planning.models import BudgetCategoryLimit
from finance.models import Transaction, ExpenseCategory

class BudgetAlertSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()
    alert_message = serializers.SerializerMethodField()

    class Meta:
        model = BudgetCategoryLimit
        fields = ['category_name', 'spending_limit', 'amount_spent', 'progress_percentage', 'status_color', 'alert_message']

    def get_progress_percentage(self, obj):
        if obj.spending_limit > 0:
            return (obj.amount_spent / obj.spending_limit) * 100
        return 0

    def get_status_color(self, obj):
        # تحديد اللون بناءً على النسبة (Orange لـ 90% و Red لـ 100%+)
        percentage = self.get_progress_percentage(obj)
        if percentage >= 100:
            return "red"
        elif percentage >= 90:
            return "orange"
        return "green"

    def get_alert_message(self, obj):
        # بناء رسالة التنبيه بناءً على السيناريو (Normal vs Exceptional)
        percentage = self.get_progress_percentage(obj)
        if percentage >= 100:
            diff = obj.amount_spent - obj.spending_limit
            return f"Budget Exceeded — {obj.category.name}! You've exceeded your ${obj.spending_limit} budget by ${diff}."
        elif percentage >= 90:
            return f"Budget Alert — {obj.category.name}: You've used {percentage:.1f}% of your budget."
        return None

class TransactionReportSerializer(serializers.ModelSerializer):
    """Serializer لعرض بيانات المعاملات داخل التقارير"""
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Transaction
        fields = ['id', 'date', 'amount', 'type', 'category_name', 'description']

class CategorySpendingSerializer(serializers.Serializer):
    """Serializer مخصص للـ Pie Chart (حسب الـ SRS في image_10e8d8.png)"""
    category = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    percentage = serializers.FloatField()


class DashboardSummarySerializer(serializers.Serializer):
    """تجهيز البيانات للـ Cards المطلوبة في الـ Normal Scenario"""
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)

    # قائمة بآخر المعاملات (Normal Scenario Step 5)
    recent_transactions = serializers.SerializerMethodField()

    # تنبيهات الميزانية (Normal Scenario Step 5)
    budget_warnings = serializers.SerializerMethodField()

    def get_recent_transactions(self, obj):
        # بنجيب آخر 5 معاملات بس عشان الـ DashboardSnapshot
        txs = Transaction.objects.filter(user=obj['user']).order_by('-date')[:5]
        from finance.serializers import TransactionSerializer  # Import هنا لتجنب الـ Circular Import
        return TransactionSerializer(txs, many=True).data

    def get_budget_warnings(self, obj):
        # عرض التحذيرات لو الميزانية قربت تخلص (Step 5)
        warnings = BudgetCategoryLimit.objects.filter(
            budget__user=obj['user'],
            amount_spent__gte=0.9 * serializers.F('spending_limit')  # 90% فأكثر
        )
        return [f"Warning: {w.category.name} is near its limit!" for w in warnings]