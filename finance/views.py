"""
Views for managing financial entities.

Provides comprehensive API endpoints for:
- Categories (predefined and custom)
- Transactions (with filtering and summaries)
- Budgets and per-category spending limits
- Savings goals with contribution tracking
- Financial reports (monthly and by category)
"""
from django.db.models import Q, Sum
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from rest_framework import serializers
from .models import Category, Transaction, Budget, BudgetCategoryLimit, SavingsGoal
from .serializers import (
    CategorySerializer,
    TransactionSerializer,
    BudgetSerializer,
    BudgetCategoryLimitSerializer,
    SavingsGoalSerializer,
)
from .services import ReportService
from decimal import Decimal


class OwnerMixin:
    """
    Mixin to restrict queryset access to the authenticated user's own data.
    
    Ensures that users can only view, update, or delete objects they created.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter the base queryset to only include items belonging to the current user.
        
        Returns:
            QuerySet: Filtered queryset.
        """
        return super().get_queryset().filter(user=self.request.user)


class CategoryViewSet(OwnerMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing transaction categories.
    
    Allows listing all categories (including global predefined ones)
    and creating/editing custom user-specific categories.
    """

    serializer_class = CategorySerializer

    def list(self, request, *args, **kwargs):
        """
        Seed default categories if none exist, then return the list.
        """
        if not Category.objects.filter(is_predefined=True).exists():
            defaults = [
                ('Food', 'expense'), ('Rent', 'expense'), ('Salary', 'income'),
                ('Transport', 'expense'), ('Health', 'expense'), ('Shopping', 'expense'),
                ('Utilities', 'expense'), ('Entertainment', 'expense')
            ]
            for name, type in defaults:
                Category.objects.get_or_create(name=name, type=type, is_predefined=True)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return user-specific categories combined with system-wide predefined categories.
        Supports filtering by 'type' query parameter.
        """
        queryset = Category.objects.filter(
            Q(user=self.request.user) | Q(is_predefined=True)
        )
        category_type = self.request.query_params.get('type')
        if category_type:
            queryset = queryset.filter(type__iexact=category_type.lower())
        return queryset

    def perform_create(self, serializer):
        """
        Assign the authenticated user to newly created categories.
        
        Args:
            serializer (CategorySerializer): The category serializer.
        """
        serializer.save(user=self.request.user)


class TransactionViewSet(OwnerMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing financial transactions.
    
    Supports comprehensive CRUD operations with advanced features:
    - **Intelligent Category Resolution**: Identify categories by ID (`category`) or by plain-text name (`category_name`).
    - **Flexible Schema**: Minimized mandatory fields to support rapid data entry.
    - **Advanced Filtering**: Narrow results by type, category, and date range.
    """

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        """
        Retrieve and filter transactions for the authenticated user.
        
        Available Filters:
        - `type`: 'expense' or 'income' (also accepts 'credit'/'debit')
        - `category`: Numeric ID or category name string
        - `date_from`: ISO date (YYYY-MM-DD)
        - `date_to`: ISO date (YYYY-MM-DD)
        - `search`: Text search against description and notes
        """
        queryset = super().get_queryset()
        params = self.request.query_params

        transaction_type = params.get('type')
        category_id = params.get('category')
        date_from = params.get('date_from')
        date_to = params.get('date_to')
        search_term = params.get('search')

        transaction_type = params.get('type')
        if transaction_type:
            transaction_type = transaction_type.lower()
            if transaction_type == 'credit':
                transaction_type = Transaction.TYPE_INCOME
            elif transaction_type == 'debit':
                transaction_type = Transaction.TYPE_EXPENSE
            queryset = queryset.filter(type=transaction_type)
        category_param = params.get('category')
        if category_param:
            if category_param.isdigit():
                queryset = queryset.filter(category_id=category_param)
            else:
                queryset = queryset.filter(category__name__iexact=category_param)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        if search_term:
            queryset = queryset.filter(
                Q(description__icontains=search_term) | 
                Q(notes__icontains=search_term)
            )

        return queryset.order_by('date', 'created_at')

    @extend_schema(
        summary="Transaction Summary",
        description="Calculate total income, expense, and balance for an optional period.",
        responses={200: inline_serializer('TransactionSummaryResponse', {'income': serializers.DecimalField(max_digits=14, decimal_places=2), 'expense': serializers.DecimalField(max_digits=14, decimal_places=2), 'balance': serializers.DecimalField(max_digits=14, decimal_places=2)})}
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Aggregate financial totals for the current user.
        
        Optionally filter by `month` and `year` query parameters to get temporal insights.
        """
        queryset = self.get_queryset()
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(date__year=year, date__month=month)

        total_income = queryset.filter(
            type=Transaction.TYPE_INCOME
        ).aggregate(total=Sum('amount'))['total'] or 0
        total_expense = queryset.filter(
            type=Transaction.TYPE_EXPENSE
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Get recent transactions (last 4)
        recent_transactions = queryset.order_by('-date', '-created_at')[:4]
        recent_serializer = TransactionSerializer(recent_transactions, many=True)

        return Response({
            'total_income': total_income,
            'total_expenses': total_expense,
            'total_balance': total_income - total_expense,
            'total_transactions': queryset.count(),
            'recent_transactions': recent_serializer.data,
        })

    @extend_schema(
        summary="Transactions by Category",
        description="Return total spending aggregated by category for a period.",
        responses={200: inline_serializer('TransactionCategorySummaryResponse', {'category_id': serializers.IntegerField(), 'category_name': serializers.CharField(), 'total': serializers.DecimalField(max_digits=14, decimal_places=2)}, many=True)}
    )
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Aggregate spending by category.
        
        Returns a list of categories and the total amount spent in each.
        """
        queryset = self.get_queryset().filter(category__isnull=False)
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(date__year=year, date__month=month)

        data = (
            queryset
            .values('category__id', 'category__name')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )
        return Response([
            {
                'category_id': item['category__id'],
                'category_name': item['category__name'],
                'total': item['total'],
            }
            for item in data
        ])


class BudgetViewSet(OwnerMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing overall monthly budgets.

    Allows setting the total spending limit for a specific month and year.
    Uses select_related('user') to avoid N+1 queries when computing the spent property.
    """

    queryset = Budget.objects.select_related('user').all()
    serializer_class = BudgetSerializer


class BudgetCategoryLimitViewSet(OwnerMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing granular spending limits within a budget.

    Allows users to assign specific portions of their total budget to individual categories.
    Uses select_related('budget__user', 'budget', 'category') to prefetch all FK relationships
    for the get_spent serializer method.
    """

    queryset = BudgetCategoryLimit.objects.all()
    serializer_class = BudgetCategoryLimitSerializer

    def get_queryset(self):
        """
        Return category limits filtered to the current user's budgets.

        Supports optional month filtering via `?month=YYYY-MM` query param.
        Uses select_related to prefetch budget, budget owner, and category.
        """
        queryset = BudgetCategoryLimit.objects.filter(
            budget__user=self.request.user
        ).select_related('budget__user', 'budget', 'category')
        month_str = self.request.query_params.get('month')
        if month_str:
            try:
                year, month = map(int, month_str.split('-'))
                queryset = queryset.filter(budget__year=year, budget__month=month)
            except (ValueError, IndexError):
                pass
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a budget limit with idempotent upsert behavior.

        If a limit already exists for the same budget+category combination,
        the limit value is updated instead of raising a duplicate error.
        Disables DRF's auto-generated unique-together validator to allow
        the view to handle the upsert logic.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        budget = serializer.validated_data.get('budget')
        category = serializer.validated_data.get('category')
        
        # Check for existing limit to avoid 400 UniqueConstraint error
        existing_limit = BudgetCategoryLimit.objects.filter(budget=budget, category=category).first()
        if existing_limit:
            existing_limit.limit = serializer.validated_data.get('limit', existing_limit.limit)
            existing_limit.save(update_fields=['limit'])
            return Response(BudgetCategoryLimitSerializer(existing_limit).data)
            
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class SavingsGoalViewSet(OwnerMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing long-term savings goals.
    
    Provides a custom 'contribute' action to add money to a goal.
    """

    queryset = SavingsGoal.objects.all()
    serializer_class = SavingsGoalSerializer

    @extend_schema(
        summary="Contribute to Goal",
        description="Add a specific amount to the current balance of a savings goal.",
        request=inline_serializer('ContributeRequest', {'amount': serializers.DecimalField(max_digits=14, decimal_places=2)}), 
        responses=SavingsGoalSerializer
    )
    @action(detail=True, methods=['post'])
    def contribute(self, request, pk=None):
        """
        Add funds to a specific savings goal.
        
        Expected Data:
            amount (Decimal): The contribution value.
            
        Returns:
            Response: The updated goal instance.
        """
        goal = self.get_object()
        amount_raw = request.data.get('amount')

        if amount_raw is None:
            return Response(
                {'error': 'amount is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = Decimal(str(amount_raw))
        except Exception:
            return Response(
                {'error': 'amount must be a valid number.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount <= 0:
            return Response(
                {'error': 'amount must be greater than zero.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        goal.add_contribution(amount)
        return Response(SavingsGoalSerializer(goal).data, status=status.HTTP_200_OK)


class ReportViewSet(viewsets.ViewSet):
    """
    ViewSet for high-level financial reports.
    
    Provides aggregated analytics about income, expenses, and category distributions.
    """

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Return basic instructions for using the report endpoints."""
        return Response({'detail': 'Use the monthly or category endpoints to fetch report data.'})

    @extend_schema(
        summary="Monthly Summary Report",
        responses={200: inline_serializer('ReportMonthlyResponse', {'income': serializers.DecimalField(max_digits=14, decimal_places=2), 'expense': serializers.DecimalField(max_digits=14, decimal_places=2), 'balance': serializers.DecimalField(max_digits=14, decimal_places=2)})}
    )
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """
        Generate a monthly financial summary.
        
        Returns:
            Response: Aggregated monthly data (Income, Expense, Balance).
        """
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        data = ReportService().monthly_summary(request.user, month, year)
        return Response(data)

    @extend_schema(
        summary="Category Distribution Report",
        responses={200: inline_serializer('ReportCategorySummaryResponse', {'category_id': serializers.IntegerField(), 'category_name': serializers.CharField(), 'total': serializers.DecimalField(max_digits=14, decimal_places=2)}, many=True)}
    )
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Generate a breakdown of spending by category for a period.
        
        Returns:
            Response: List of categories with total amounts spent in each.
        """
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        data = ReportService().category_summary(request.user, month, year)
        return Response(data)
