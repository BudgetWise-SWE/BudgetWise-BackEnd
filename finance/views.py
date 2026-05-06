"""
Views for managing financial entities including transactions, budgets, and categories.
"""
from django.db.models import Q, Sum
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Transaction, Budget, BudgetCategoryLimit, SavingsGoal
from .serializers import (
    CategorySerializer,
    TransactionSerializer,
    BudgetSerializer,
    BudgetCategoryLimitSerializer,
    SavingsGoalSerializer,
)
from .services import ReportService

class OwnerMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

class CategoryViewSet(OwnerMixin, viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(Q(user=self.request.user) | Q(is_predefined=True))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TransactionViewSet(OwnerMixin, viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    @action(detail=False, methods=['get'])
    def summary(self, request):
        queryset = self.get_queryset()
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(date__year=year, date__month=month)
        total_income = queryset.filter(type=Transaction.TYPE_INCOME).aggregate(total=Sum('amount'))['total'] or 0
        total_expense = queryset.filter(type=Transaction.TYPE_EXPENSE).aggregate(total=Sum('amount'))['total'] or 0
        return Response({
            'income': total_income,
            'expense': total_expense,
            'balance': total_income - total_expense,
        })

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        queryset = self.get_queryset().filter(category__isnull=False)
        data = queryset.values('category__id', 'category__name').annotate(total=Sum('amount')).order_by('-total')
        return Response([
            {
                'category_id': item['category__id'],
                'category_name': item['category__name'],
                'total': item['total'],
            }
            for item in data
        ])

class BudgetViewSet(OwnerMixin, viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer

class BudgetCategoryLimitViewSet(OwnerMixin, viewsets.ModelViewSet):
    queryset = BudgetCategoryLimit.objects.all()
    serializer_class = BudgetCategoryLimitSerializer

    def get_queryset(self):
        return super().get_queryset().filter(budget__user=self.request.user)

class SavingsGoalViewSet(OwnerMixin, viewsets.ModelViewSet):
    queryset = SavingsGoal.objects.all()
    serializer_class = SavingsGoalSerializer

class ReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response({'detail': 'Use the monthly or category endpoints to fetch report data.'})

    @action(detail=False, methods=['get'])
    def monthly(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        data = ReportService().monthly_summary(request.user, month, year)
        return Response(data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        data = ReportService().category_summary(request.user, month, year)
        return Response(data)
