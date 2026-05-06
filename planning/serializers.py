from datetime import date
from rest_framework import serializers
from finance.models import Budget, BudgetCategoryLimit, SavingsGoal, Category
from django.utils import timezone

class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetCategoryLimit
        fields = ['category', 'limit']

    def validate_limit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive number.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        category = validated_data['category']
        now = timezone.now()

        budget_parent, _ = Budget.objects.get_or_create(
            user=user,
            month=now.month,
            year=now.year
        )

        if BudgetCategoryLimit.objects.filter(budget=budget_parent, category=category).exists():
            raise serializers.ValidationError(
                "A budget for this category already exists for this month. Please edit the existing budget instead."
            )

        return BudgetCategoryLimit.objects.create(budget=budget_parent, **validated_data)


class SavingsGoalSerializer(serializers.ModelSerializer):
    monthly_savings_needed = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            'id', 'name', 'target_amount', 'current_amount',
            'deadline', 'completed', 'monthly_savings_needed', 'progress_percentage'
        ]
        read_only_fields = ['id', 'current_amount']

    def get_monthly_savings_needed(self, obj):
        today = date.today()
        remaining = obj.target_amount - obj.current_amount
        if remaining <= 0: return 0

        months = (obj.deadline.year - today.year) * 12 + (obj.deadline.month - today.month)
        return round(remaining / max(months, 1), 2)

    def get_progress_percentage(self, obj):
        if obj.target_amount > 0:
            return round((obj.current_amount / obj.target_amount) * 100, 2)
        return 0