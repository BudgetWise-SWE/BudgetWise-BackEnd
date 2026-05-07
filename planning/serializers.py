from datetime import date
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from finance.models import Budget, BudgetCategoryLimit, SavingsGoal
from django.utils import timezone


class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    """Serializer for creating a category spending limit for the current month's budget."""

    class Meta:
        model = BudgetCategoryLimit
        fields = ['category', 'limit']

    def validate_limit(self, value):
        """Ensure the limit is a positive number."""
        if value <= 0:
            raise serializers.ValidationError('Amount must be a positive number.')
        return value

    def create(self, validated_data):
        """
        Create or retrieve the current month's budget for the user,
        then create the category limit within it.
        Raises validation error if a limit for this category already exists this month.
        """
        user = self.context['request'].user
        category = validated_data['category']
        now = timezone.now()

        budget_parent, _ = Budget.objects.get_or_create(
            user=user,
            month=now.month,
            year=now.year,
            defaults={'name': f'Budget {now.month}/{now.year}', 'total_limit': 0},
        )

        if BudgetCategoryLimit.objects.filter(budget=budget_parent, category=category).exists():
            raise serializers.ValidationError(
                'A budget for this category already exists for this month. '
                'Please edit the existing budget instead.'
            )

        return BudgetCategoryLimit.objects.create(budget=budget_parent, **validated_data)


class SavingsGoalSerializer(serializers.ModelSerializer):
    """Serializer for savings goals with computed monthly savings needed and progress percentage."""

    monthly_savings_needed = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            'id', 'name', 'target_amount', 'current_amount',
            'deadline', 'completed', 'monthly_savings_needed', 'progress_percentage',
        ]
        read_only_fields = ['id', 'current_amount', 'completed']

    def get_monthly_savings_needed(self, obj):
        """Calculate how much the user needs to save per month to reach the goal by the deadline."""
        if not obj.deadline:
            return None
        today = date.today()
        remaining = obj.target_amount - obj.current_amount
        if remaining <= 0:
            return 0
        months = (obj.deadline.year - today.year) * 12 + (obj.deadline.month - today.month)
        return round(remaining / max(months, 1), 2)

    def get_progress_percentage(self, obj):
        """Return the percentage of the target amount that has been saved."""
        if obj.target_amount > 0:
            return round((obj.current_amount / obj.target_amount) * 100, 2)
        return 0