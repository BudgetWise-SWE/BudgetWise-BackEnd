from datetime import date
from rest_framework import serializers
from .models import Budget, BudgetCategoryLimit, SavingsGoal
from finance.models import ExpenseCategory
from django.utils import timezone

class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetCategoryLimit
        fields = ['category', 'spending_limit']

    def validate_spending_limit(self, value):
        # Step 7: التأكد إن الرقم موجب
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive number.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        category = validated_data['category']
        now = timezone.now()

        # Step 5: Period defaults to current month[cite: 2]
        budget_parent, _ = Budget.objects.get_or_create(
            user=user,
            month=now.month,
            year=now.year
        )

        # Exceptional Scenario: منع التكرار لنفس الـ category[cite: 2]
        if BudgetCategoryLimit.objects.filter(budget=budget_parent, category=category).exists():
            raise serializers.ValidationError(
                "A budget for this category already exists for this month. Please edit the existing budget instead."
            )

        return BudgetCategoryLimit.objects.create(budget=budget_parent, **validated_data)


class SavingsGoalSerializer(serializers.ModelSerializer):
    # حقول إضافية مش في الداتابيز بس مهمة للـ Frontend (US #6)
    monthly_savings_needed = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            'goal_id', 'name', 'target_amount', 'current_saved',
            'deadline', 'status', 'monthly_savings_needed', 'progress_percentage'
        ]
        read_only_fields = ['goal_id', 'current_saved']

    def get_monthly_savings_needed(self, obj):
        # حساب المبلغ المطلوب توفيره شهرياً للوصول للهدف
        today = date.today()
        remaining = obj.target_amount - obj.current_saved
        if remaining <= 0: return 0

        # فرق الشهور بين النهاردة والـ deadline
        months = (obj.deadline.year - today.year) * 12 + (obj.deadline.month - today.month)
        return round(remaining / max(months, 1), 2)

    def get_progress_percentage(self, obj):
        # حساب النسبة المئوية للـ progress bar (Step 10)[cite: 2]
        if obj.target_amount > 0:
            return round((obj.current_saved / obj.target_amount) * 100, 2)
        return 0