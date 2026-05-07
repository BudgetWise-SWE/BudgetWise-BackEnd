"""
Views for managing financial entities: categories, transactions,
budgets, budget category limits, savings goals, and reports.
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
    """Mixin that restricts all queryset access to the authenticated user's own objects."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to only the objects belonging to the requesting user."""
        return super().get_queryset().filter(user=self.request.user)


class CategoryViewSet(OwnerMixin, viewsets.ModelViewSet):
    """CRUD operations for transaction categories (predefined + user-created)."""

    serializer_class = CategorySerializer

    def get_queryset(self):
        """Return both the user's own categories and all predefined system categories."""
        return Category.objects.filter(
            Q(user=self.request.user) | Q(is_predefined=True)
        )

    def perform_create(self, serializer):
        """Assign the authenticated user to the new category."""
        serializer.save(user=self.request.user)


class TransactionViewSet(OwnerMixin, viewsets.ModelViewSet):
    """CRUD operations for transactions with optional filtering."""

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        """Return the user's transactions with optional filters applied."""
        queryset = super().get_queryset()
        params = self.request.query_params

        transaction_type = params.get('type')
        category_id = params.get('category')
        date_from = params.get('date_from')
        date_to = params.get('date_to')

        if transaction_type:
            queryset = queryset.filter(type=transaction_type)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset

    @extend_schema(responses={200: inline_serializer('TransactionSummaryResponse', {'income': serializers.DecimalField(max_digits=14, decimal_places=2), 'expense': serializers.DecimalField(max_digits=14, decimal_places=2), 'balance': serializers.DecimalField(max_digits=14, decimal_places=2)})})
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Return income, expense, and balance totals for an optional month/year period."""
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

        return Response({
            'income': total_income,
            'expense': total_expense,
            'balance': total_income - total_expense,
        })

    @extend_schema(responses={200: inline_serializer('TransactionCategorySummaryResponse', {'category_id': serializers.IntegerField(), 'category_name': serializers.CharField(), 'total': serializers.DecimalField(max_digits=14, decimal_places=2)}, many=True)})
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Return total spending aggregated by category for an optional month/year period."""
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
    """CRUD operations for monthly budgets."""

    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer


class BudgetCategoryLimitViewSet(OwnerMixin, viewsets.ModelViewSet):
    """CRUD operations for per-category spending limits within a budget."""

    queryset = BudgetCategoryLimit.objects.all()
    serializer_class = BudgetCategoryLimitSerializer

    def get_queryset(self):
        """Filter limits to only those belonging to the authenticated user's budgets."""
        return BudgetCategoryLimit.objects.filter(budget__user=self.request.user)


class SavingsGoalViewSet(OwnerMixin, viewsets.ModelViewSet):
    """CRUD operations for savings goals with a contribute action."""

    queryset = SavingsGoal.objects.all()
    serializer_class = SavingsGoalSerializer

    @extend_schema(request=inline_serializer('ContributeRequest', {'amount': serializers.DecimalField(max_digits=14, decimal_places=2)}), responses=SavingsGoalSerializer)
    @action(detail=True, methods=['post'])
    def contribute(self, request, pk=None):
        """Add a contribution amount to a specific savings goal."""
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
    """ViewSet for financial reports — monthly summary and category breakdown."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Return a hint about the available report sub-endpoints."""
        return Response({'detail': 'Use the monthly or category endpoints to fetch report data.'})

    @extend_schema(responses={200: inline_serializer('ReportMonthlyResponse', {'income': serializers.DecimalField(max_digits=14, decimal_places=2), 'expense': serializers.DecimalField(max_digits=14, decimal_places=2), 'balance': serializers.DecimalField(max_digits=14, decimal_places=2)})})
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Return monthly income, expense, and balance summary."""
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        data = ReportService().monthly_summary(request.user, month, year)
        return Response(data)

    @extend_schema(responses={200: inline_serializer('ReportCategorySummaryResponse', {'category_id': serializers.IntegerField(), 'category_name': serializers.CharField(), 'total': serializers.DecimalField(max_digits=14, decimal_places=2)}, many=True)})
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Return spending totals grouped by category for the specified period."""
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        data = ReportService().category_summary(request.user, month, year)
        return Response(data)
