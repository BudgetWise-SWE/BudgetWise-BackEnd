"""
Serializers for the finance application.

Handles validation and data conversion for categories, transactions,
budgets, and savings goals. Includes business logic for linking
transactions to the current user and service layer.
"""
from rest_framework import serializers
from .models import Category, Transaction, Budget, BudgetCategoryLimit, SavingsGoal
from .services import TransactionService


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for expense and income categories.
    
    Automatically handles user assignment and category type identification.
    """

    class Meta:
        """Metadata for CategorySerializer."""
        model = Category
        fields = ['id', 'name', 'type', 'parent', 'is_predefined', 'created_at']
        read_only_fields = ['is_predefined', 'created_at']

    def create(self, validated_data):
        """
        Create a new custom category.
        
        Args:
            validated_data (dict): Validated input data.
            
        Returns:
            Category: Created category instance with authenticated user attached.
        """
        validated_data['user'] = self.context['request'].user
        validated_data['is_predefined'] = False
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for logging financial transactions.
    
    Includes validation for amounts, category matching, and income requirements.
    """

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        """Metadata for TransactionSerializer."""
        model = Transaction
        fields = [
            'id', 'type', 'category', 'category_name',
            'amount', 'date', 'description', 'notes', 'source', 'created_at',
        ]
        read_only_fields = ['created_at', 'category_name']

    def validate(self, data):
        """
        Perform complex cross-field validation.
        
        Checks:
        1. Amount is positive.
        2. Transaction type matches the chosen category's type.
        3. Income transactions have a source defined.
        
        Args:
            data (dict): Input data to validate.
            
        Returns:
            dict: Validated data.
            
        Raises:
            serializers.ValidationError: If any business rule is violated.
        """
        amount = data.get('amount')
        transaction_type = data.get('type')
        category = data.get('category')
        source = data.get('source', '')

        if amount is None or amount <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        if category is not None and category.type != transaction_type:
            raise serializers.ValidationError('Category type must match transaction type.')
        if transaction_type == Transaction.TYPE_INCOME and not source:
            raise serializers.ValidationError('Income transactions require a source.')
        return data

    def create(self, validated_data):
        """
        Create a transaction via the TransactionService.
        
        Delegates to the service layer to handle side effects like
        budget limit updates and notification triggers.
        
        Args:
            validated_data (dict): Validated input data.
            
        Returns:
            Transaction: The created transaction instance.
        """
        transaction = TransactionService().create_transaction(self.context['request'].user, validated_data)
        return transaction


class BudgetSerializer(serializers.ModelSerializer):
    """
    Serializer for monthly budgets.
    
    Computes real-time 'spent' and 'remaining' values based on transaction history.
    """

    spent = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    remaining = serializers.SerializerMethodField()

    class Meta:
        """Metadata for BudgetSerializer."""
        model = Budget
        fields = [
            'id', 'name', 'month', 'year', 'total_limit',
            'spent', 'remaining', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at', 'spent', 'remaining']

    def get_remaining(self, obj):
        """
        Calculate available budget balance.
        
        Args:
            obj (Budget): The budget instance.
            
        Returns:
            Decimal: remaining amount (total_limit - spent).
        """
        remaining = obj.total_limit - obj.spent
        return max(remaining, 0)

    def create(self, validated_data):
        """
        Establish a new budget for the authenticated user.
        
        Args:
            validated_data (dict): Validated input data.
            
        Returns:
            Budget: Newly created budget instance.
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    """
    Serializer for assigning limits to specific categories within a budget.
    """

    remaining = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        """Metadata for BudgetCategoryLimitSerializer."""
        model = BudgetCategoryLimit
        fields = ['id', 'budget', 'category', 'category_name', 'limit', 'spent', 'remaining', 'status']
        read_only_fields = ['spent', 'status', 'remaining', 'category_name']


class SavingsGoalSerializer(serializers.ModelSerializer):
    """
    Serializer for user-defined savings targets.
    
    Computes the 'progress' percentage based on target vs current amounts.
    """

    progress = serializers.IntegerField(read_only=True)

    class Meta:
        """Metadata for SavingsGoalSerializer."""
        model = SavingsGoal
        fields = [
            'id', 'name', 'target_amount', 'current_amount',
            'deadline', 'completed', 'progress', 'created_at',
        ]
        read_only_fields = ['completed', 'progress', 'created_at', 'current_amount']

    def create(self, validated_data):
        """
        Register a new savings goal for the current user.
        
        Args:
            validated_data (dict): Validated input data.
            
        Returns:
            SavingsGoal: Created instance.
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
