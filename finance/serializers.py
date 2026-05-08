"""
Serializers for the finance application.

Handles validation and data conversion for categories, transactions,
budgets, and savings goals. Includes business logic for linking
transactions to the current user and service layer.

"""
from django.db import models
from django.db.models import Q
from django.utils.dateparse import parse_date
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
        fields = ['id', 'name', 'type', 'is_predefined', 'created_at']
        read_only_fields = ['is_predefined', 'created_at']

    def validate_type(self, value):
        """Normalize type to lowercase."""
        if value:
            return value.lower()
        return value

    def create(self, validated_data):
        """
        Mark new categories as non-predefined.
        User assignment is handled by the view's perform_create.
        """
        validated_data['is_predefined'] = False
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    """
    Handles serialization and validation for financial transactions.
    
    Key Features:
    - Supports `category_name` for intuitive creation via text instead of IDs.
    - Implements intelligent fallbacks (e.g., 'Other' category) for resilient data entry.
    - Enforces minimal mandatory fields to support rapid financial logging.
    """

    category_name = serializers.CharField(required=False, write_only=True)
    category_display_name = serializers.CharField(source='category.name', read_only=True)
    name = serializers.CharField(source='description', required=False)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    date = serializers.DateField(required=False)
    amountOfMoney = serializers.SerializerMethodField()
    dataOfTransaction = serializers.DateField(source='date', required=False, read_only=True)

    class Meta:
        """Metadata for TransactionSerializer."""
        model = Transaction
        fields = [
            'id', 'type', 'category', 'category_name', 'category_display_name',
            'amount', 'amountOfMoney', 'date', 'dataOfTransaction', 'description', 
            'name', 'notes', 'source', 'created_at',
        ]
        read_only_fields = ['created_at']

    def validate(self, data):
        """
        Validate and enrich transaction data.
        
        Logic:
        1. Resolves `category_name` to a formal Category instance if `category` ID is missing.
        2. Ensures the transaction type (income/expense) matches the category.
        3. Defaults missing categories to 'Other' to ensure data capture.
        """
        user = self.context['request'].user
        amount = data.get('amount')
        transaction_type = data.get('type')
        if transaction_type:
            transaction_type = transaction_type.lower()
            data['type'] = transaction_type
            
        category = data.get('category')
        category_name = data.pop('category_name', None)

        if amount is None or amount <= 0:
            raise serializers.ValidationError({'amount': 'Amount must be greater than zero.'})

        # Resolve category by name if not provided by ID
        if category is None and category_name:
            category_name = category_name.strip()
            # Search in user-specific categories or predefined ones
            category = Category.objects.filter(
                models.Q(user=user) | models.Q(is_predefined=True),
                name__iexact=category_name,
                type=transaction_type
            ).first()
            
            if not category:
                # [NEW LOGIC] Create the category on the fly if it doesn't exist
                category = Category.objects.create(
                    user=user,
                    name=category_name,
                    type=transaction_type,
                    is_predefined=False
                )
            
            data['category'] = category

        if data.get('category') and data.get('category').type != transaction_type:
            raise serializers.ValidationError({'category': 'Category type must match transaction type.'})

        return data

    def get_amountOfMoney(self, obj):
        """
        Return negated amount for expenses to match frontend expectations.
        """
        if obj.type == Transaction.TYPE_EXPENSE:
            return -obj.amount
        return obj.amount

    def to_internal_value(self, data):
        """
        Handle frontend field aliases and typo normalization.

        - Maps amountOfMoney -> amount, dataOfTransaction -> date, name -> description
        - Converts string category names to category_name for text-based resolution
        - Normalizes 'Heath' typo to 'Health' for category matching
        """
        if 'amountOfMoney' in data and 'amount' not in data:
            data['amount'] = data['amountOfMoney']
        if 'dataOfTransaction' in data and 'date' not in data:
            data['date'] = data['dataOfTransaction']
        if 'name' in data and 'description' not in data:
            data['description'] = data['name']
        if 'category' in data and isinstance(data['category'], str) and not data['category'].isdigit():
            cat_val = data['category'].strip()
            # Handle frontend typo 'Heath' in submission
            if cat_val == "Heath":
                cat_val = "Health"
            data['category_name'] = cat_val
            # Remove from data to prevent ID lookup error if it's not an integer
            new_data = data.copy()
            del new_data['category']
            return super().to_internal_value(new_data)
            
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """
        Format response for frontend compatibility.

        - Capitalizes the 'type' field
        - Formats date as 'Mon DD, YYYY'
        - Null-coalesces notes, name, description to empty strings
        - Returns category name instead of ID
        - Reverses 'Health' -> 'Heath' to match frontend color map
        """
        representation = super().to_representation(instance)
        if representation.get('type'):
            representation['type'] = representation['type'].capitalize()

        # [FRONTEND ALIGNMENT] Format date to match hardcoded UI style (e.g., Jun 14, 2023)
        if instance.date:
            representation['dataOfTransaction'] = instance.date.strftime('%b %d, %Y')
            
        # [FRONTEND ALIGNMENT] Ensure display fields are strings, not null
        if representation.get('notes') is None:
            representation['notes'] = ""
        if representation.get('name') is None:
            representation['name'] = ""
        if representation.get('description') is None:
            representation['description'] = ""
            
        # [FRONTEND ALIGNMENT] Category must be the name string, not ID, for storage.js logic
        if instance.category:
            cat_name = instance.category.name
            # Handle frontend typo 'Heath' in storage.js colors map
            if cat_name == "Health":
                cat_name = "Heath"
            representation['category'] = cat_name

        return representation

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
    month = serializers.IntegerField(required=False)
    year = serializers.IntegerField(required=False)

    class Meta:
        """Metadata for BudgetSerializer."""
        model = Budget
        fields = [
            'id', 'name', 'month', 'year', 'total_limit',
            'spent', 'remaining', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'created_at', 'updated_at', 'spent', 'remaining']

    def validate(self, data):
        """
        Support 'month' as 'YYYY-MM' string from the frontend.
        """
        request = self.context.get('request')
        if request and 'month' in request.data and isinstance(request.data['month'], str) and '-' in request.data['month']:
            try:
                year_str, month_str = request.data['month'].split('-')
                data['year'] = int(year_str)
                data['month'] = int(month_str)
            except (ValueError, IndexError):
                raise serializers.ValidationError({'month': 'Invalid month format. Use YYYY-MM.'})
        
        if not data.get('month') or not data.get('year'):
            if not request or request.method == 'POST':
                raise serializers.ValidationError({'month': 'Month and Year are required.'})

        return data

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
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BudgetCategoryLimitSerializer(serializers.ModelSerializer):
    """
    Serializer for assigning limits to specific categories within a budget.
    
    Supports direct creation via 'month' (YYYY-MM) and 'category_name'
    to align with frontend logic.
    """

    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    category_name = serializers.CharField(required=False)
    month = serializers.CharField(write_only=True, required=False)

    class Meta:
        """Metadata for BudgetCategoryLimitSerializer."""
        model = BudgetCategoryLimit
        fields = ['id', 'budget', 'category', 'category_name', 'month', 'limit', 'spent', 'remaining', 'status']
        read_only_fields = ['status']
        validators = []  # UniqueConstraint handled in view's create() for upsert logic

    def get_spent(self, obj):
        """
        Calculate real-time spent amount from transactions for this category/budget period.

        Result is cached on the instance via _cached_spent to avoid redundant
        queries when both spent and remaining are serialized.
        """
        if not hasattr(obj, '_cached_spent'):
            from django.db.models import Sum
            from .models import Transaction
            obj._cached_spent = Transaction.objects.filter(
                user=obj.budget.user,
                category=obj.category,
                type=Transaction.TYPE_EXPENSE,
                date__year=obj.budget.year,
                date__month=obj.budget.month
            ).aggregate(total=Sum('amount'))['total'] or 0
        return obj._cached_spent

    def get_remaining(self, obj):
        """
        Calculate remaining budget for this category limit.

        Uses the cached spent value from get_spent to avoid extra queries.
        """
        return max(obj.limit - self.get_spent(obj), 0)

    def to_representation(self, instance):
        """
        Return category name instead of ID for frontend display logic.
        """
        representation = super().to_representation(instance)
        if instance.category:
            representation['category'] = instance.category.name
        return representation

    def validate(self, data):
        """
        Resolve budget and category from month and category_name if IDs are missing.
        """
        request = self.context.get('request')
        user = request.user
        category_name = data.get('category_name')
        if category_name:
            category_name = category_name.strip()
        month_str = data.pop('month', None)
        
        # 1. Resolve Category
        if not data.get('category') and category_name:
            category = Category.objects.filter(
                Q(user=user) | Q(is_predefined=True),
                name__iexact=category_name,
                type=Category.TYPE_EXPENSE
            ).first()
            if not category:
                # Create category if it doesn't exist (assuming expense for budget)
                category = Category.objects.create(
                    user=user,
                    name=category_name,
                    type=Category.TYPE_EXPENSE
                )
            data['category'] = category

        # 2. Resolve/Create Budget container for the month
        if not data.get('budget') and month_str:
            try:
                year, month = map(int, month_str.split('-'))
                budget, _ = Budget.objects.get_or_create(
                    user=user,
                    year=year,
                    month=month,
                    defaults={'name': f"{month_str} Budget", 'total_limit': 0}
                )
                data['budget'] = budget
            except (ValueError, IndexError):
                raise serializers.ValidationError({'month': 'Invalid month format. Use YYYY-MM.'})

        return data

    def create(self, validated_data):
        """
        Remove 'category_name' from validated_data before creating the instance.
        """
        validated_data.pop('category_name', None)
        return super().create(validated_data)


class SavingsGoalSerializer(serializers.ModelSerializer):
    """
    Serializer for user-defined savings targets.
    
    Computes the 'progress' percentage based on target vs current amounts.
    """

    progress = serializers.IntegerField(read_only=True)
    target = serializers.DecimalField(source='target_amount', max_digits=14, decimal_places=2, required=False)
    saved = serializers.DecimalField(source='current_amount', max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        """Metadata for SavingsGoalSerializer."""
        model = SavingsGoal
        fields = [
            'id', 'name', 'target_amount', 'target', 'current_amount', 'saved',
            'deadline', 'completed', 'progress', 'created_at',
        ]
        read_only_fields = ['completed', 'progress', 'created_at', 'current_amount', 'saved']


    def to_representation(self, instance):
        """
        Add UI-specific fields for frontend parity.
        """
        representation = super().to_representation(instance)
        
        # 1. Format deadline as YYYY-MM
        if instance.deadline:
            representation['deadline'] = instance.deadline.strftime('%Y-%m')
            
        # 2. Add status
        representation['status'] = "completed" if instance.completed else "in-progress"
        
        # 3. Derive icon and iconType from name (matching savings.js logic)
        name = instance.name.lower()
        icon_map = {
            'emergency': ('security', 'emergency'),
            'vacation': ('beach_access', 'vacation'),
            'travel': ('flight', 'vacation'),
            'house': ('home', 'home'),
            'home': ('home', 'home'),
            'car': ('directions_car', 'tech'),
            'laptop': ('computer', 'tech'),
            'computer': ('computer', 'tech'),
        }
        
        icon = 'savings'
        icon_type = 'emergency'
        
        for key, (i, it) in icon_map.items():
            if key in name:
                icon = i
                icon_type = it
                break
                
        representation['icon'] = icon
        representation['iconType'] = icon_type
        
        return representation

    def validate(self, data):
        """
        Support 'deadline' as 'YYYY-MM' string from the frontend.
        """
        request = self.context.get('request')
        if request and 'deadline' in request.data and isinstance(request.data['deadline'], str) and len(request.data['deadline']) == 7:
            try:
                deadline_str = request.data['deadline'] + "-01"
                data['deadline'] = parse_date(deadline_str)
            except (ValueError, IndexError):
                raise serializers.ValidationError({'deadline': 'Invalid deadline format. Use YYYY-MM.'})
        return data

    def create(self, validated_data):
        """
        Register a new savings goal for the current user.
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
