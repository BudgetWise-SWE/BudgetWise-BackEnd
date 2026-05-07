"""
Serializers for the planning application.

Handles the logic for setting category spending limits (auto-mapping to the
current active budget) and calculating savings targets based on deadlines.
"""
from datetime import date
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from finance.models import Budget, BudgetCategoryLimit, SavingsGoal
from django.utils import timezone


class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    """
    Serializer for establishing a category spending limit for the current month.
    
    This serializer is specialized for 'Quick Planning' where the system
    automatically finds or creates the current month's budget container.
    """

    class Meta:
        """Metadata for BudgetCategoryLimitSerializer."""
        model = BudgetCategoryLimit
        fields = ['category', 'limit']

    def validate_limit(self, value):
        """
        Ensure the limit provided is a positive number.
        
        Args:
            value (Decimal): The input limit value.
            
        Returns:
            Decimal: Validated limit.
            
        Raises:
            serializers.ValidationError: If the value is non-positive.
        """
        if value <= 0:
            raise serializers.ValidationError('Amount must be a positive number.')
        return value

    def create(self, validated_data):
        """
        Link the category limit to the current month's budget.
        
        Automatically finds or creates a Budget instance for the current
        month/year and attaches the new limit to it.
        
        Args:
            validated_data (dict): Validated input data.
            
        Returns:
            BudgetCategoryLimit: Created instance.
            
        Raises:
            serializers.ValidationError: If a limit for the category already exists for the month.
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
    """
    Serializer for savings goals with advanced planning metrics.
    
    Computes 'monthly_savings_needed' based on the distance to the deadline
    and the remaining target amount.
    """

    monthly_savings_needed = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        """Metadata for SavingsGoalSerializer."""
        model = SavingsGoal
        fields = [
            'id', 'name', 'target_amount', 'current_amount',
            'deadline', 'completed', 'monthly_savings_needed', 'progress_percentage',
        ]
        read_only_fields = ['id', 'current_amount', 'completed']

    def get_monthly_savings_needed(self, obj):
        """
        Calculate the required monthly contribution to reach the goal by its deadline.
        
        Returns:
            float: Amount needed per month, or None if no deadline is set.
        """
        if not obj.deadline:
            return None
        today = date.today()
        remaining = obj.target_amount - obj.current_amount
        if remaining <= 0:
            return 0
        months = (obj.deadline.year - today.year) * 12 + (obj.deadline.month - today.month)
        return round(remaining / max(months, 1), 2)

    def get_progress_percentage(self, obj):
        """
        Calculate the percentage completion of the savings goal.
        
        Returns:
            float: Percentage value rounded to 2 decimal places.
        """
        if obj.target_amount > 0:
            return round((obj.current_amount / obj.target_amount) * 100, 2)
        return 0