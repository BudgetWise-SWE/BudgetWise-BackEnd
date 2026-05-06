from rest_framework import serializers
from .models import Category, Transaction, Budget, BudgetCategoryLimit, SavingsGoal
from .services import TransactionService

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type', 'parent', 'is_predefined', 'created_at']
        read_only_fields = ['is_predefined', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['is_predefined'] = False
        return super().create(validated_data)

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'type', 'category', 'amount', 'date', 'description', 'notes', 'source', 'created_at']
        read_only_fields = ['created_at']

    def validate(self, data):
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
        validated_data['user'] = self.context['request'].user
        transaction = TransactionService().create_transaction(self.context['request'].user, validated_data)
        return transaction

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ['id', 'name', 'month', 'year', 'total_limit', 'status', 'created_at', 'updated_at']
        read_only_fields = ['status', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetCategoryLimit
        fields = ['id', 'budget', 'category', 'limit', 'spent', 'status']
        read_only_fields = ['spent', 'status']

class SavingsGoalSerializer(serializers.ModelSerializer):
    progress = serializers.IntegerField(source='progress', read_only=True)

    class Meta:
        model = SavingsGoal
        fields = ['id', 'name', 'target_amount', 'current_amount', 'deadline', 'completed', 'progress', 'created_at']
        read_only_fields = ['completed', 'progress', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
