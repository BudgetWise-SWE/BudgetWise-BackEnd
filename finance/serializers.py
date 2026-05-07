from rest_framework import serializers
from .models import Category, Transaction, Budget, BudgetCategoryLimit, SavingsGoal
from .services import TransactionService


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for expense/income categories."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'type', 'parent', 'is_predefined', 'created_at']
        read_only_fields = ['is_predefined', 'created_at']

    def create(self, validated_data):
        """Attach the authenticated user and mark the category as custom."""
        validated_data['user'] = self.context['request'].user
        validated_data['is_predefined'] = False
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for financial transactions."""

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'type', 'category', 'category_name',
            'amount', 'date', 'description', 'notes', 'source', 'created_at',
        ]
        read_only_fields = ['created_at', 'category_name']

    def validate(self, data):
        """Validate amount, category type consistency, and income source requirement."""
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
        """Create a transaction and trigger budget processing via the service layer."""
        # User is attached in the service layer
        transaction = TransactionService().create_transaction(self.context['request'].user, validated_data)
        return transaction


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for monthly budgets, including computed spent and remaining fields."""

    spent = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    remaining = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'month', 'year', 'total_limit',
            'spent', 'remaining', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at', 'spent', 'remaining']

    def get_remaining(self, obj):
        """Return the remaining budget amount (total_limit minus spent)."""
        remaining = obj.total_limit - obj.spent
        return max(remaining, 0)

    def create(self, validated_data):
        """Attach the authenticated user to the budget on creation."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    """Serializer for per-category spending limits within a budget."""

    remaining = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = BudgetCategoryLimit
        fields = ['id', 'budget', 'category', 'category_name', 'limit', 'spent', 'remaining', 'status']
        read_only_fields = ['spent', 'status', 'remaining', 'category_name']


class SavingsGoalSerializer(serializers.ModelSerializer):
    """Serializer for savings goals including computed progress fields."""

    progress = serializers.IntegerField(read_only=True)

    class Meta:
        model = SavingsGoal
        fields = [
            'id', 'name', 'target_amount', 'current_amount',
            'deadline', 'completed', 'progress', 'created_at',
        ]
        read_only_fields = ['completed', 'progress', 'created_at', 'current_amount']

    def create(self, validated_data):
        """Attach the authenticated user to the savings goal on creation."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
