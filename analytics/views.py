"""
Views for the analytics application.

Provides endpoints for tracking budget status alerts, generating
spending reports with charts, and retrieving dashboard summaries.
"""
from django.db.models import Sum
from rest_framework.views import APIView
from decimal import Decimal
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from finance.models import BudgetCategoryLimit, Transaction
from .serializers import BudgetAlertSerializer, CategorySpendingSerializer, DashboardSummarySerializer
from django.utils import timezone


class BudgetStatusView(APIView):
    """
    Retrieves the status of all budget category limits for the current month.
    
    Returns a list of alerts including spending progress and warning messages.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Current Budget Status Alerts",
        description="List all budget category limits for the authenticated user's current month.",
        responses=BudgetAlertSerializer(many=True)
    )
    def get(self, request):
        """
        Handle GET requests for budget alerts.
        
        Returns:
            Response: List of budget status alerts.
        """
        now = timezone.now()
        active_limits = BudgetCategoryLimit.objects.filter(
            budget__user=request.user,
            budget__month=now.month,
            budget__year=now.year,
        )
        serializer = BudgetAlertSerializer(active_limits, many=True)
        return Response(serializer.data)


class ReportsAnalyticsView(APIView):
    """
    Generates detailed spending analytics for a specific date range.
    
    Provides data suitable for pie charts (category distribution) and
    bar charts (income vs expense).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Spending Analytics Reports",
        operation_id="get_reports_analytics",
        description="Return category spending breakdown and income vs expense totals."
    )
    def get(self, request):
        """
        Return category spending breakdown and income vs expense totals.

        Query parameters:
            start_date (str): Start of the date range (YYYY-MM-DD). Defaults to first of current month.
            end_date (str): End of the date range (YYYY-MM-DD). Defaults to today.
            
        Returns:
            Response: Analytics data including pie chart and bar chart aggregates.
        """
        start_date = request.query_params.get('start_date', timezone.now().date().replace(day=1))
        end_date = request.query_params.get('end_date', timezone.now().date())

        transactions = Transaction.objects.filter(
            user=request.user,
            date__range=[start_date, end_date],
        )

        if not transactions.exists():
            return Response({
                'message': 'No transaction data available for this period.',
                'pie_chart': [],
                'bar_chart': {},
                'insight': 'Start logging your expenses to see analytics!',
            })

        total_expenses = transactions.filter(
            type='expense'
        ).aggregate(Sum('amount'))['amount__sum'] or 1

        # Use raw SQL to get optimized category spending breakdown
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT c.name, SUM(t.amount)
                FROM finance_transaction t
                JOIN finance_category c ON t.category_id = c.id
                WHERE t.user_id = %s AND t.type = %s AND t.date BETWEEN %s AND %s
                GROUP BY c.name
            ''', [request.user.id, 'expense', start_date, end_date])
            
            spending_by_category = [
                {'category__name': row[0], 'total_spent': row[1]}
                for row in cursor.fetchall()
            ]

        pie_data = [
            {
                'category': item['category__name'],
                'total_spent': item['total_spent'],
                'percentage': round((item['total_spent'] / total_expenses) * 100, 2),
            }
            for item in spending_by_category
        ]

        total_income = transactions.filter(
            type='income'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        # Simple financial health insight
        insight = (
            'Your spending is above 90% of your income — consider cutting back.'
            if total_expenses > (total_income * Decimal('0.9'))
            else 'Good job! Your spending is within a healthy range.'
        )

        return Response({
            'pie_chart': CategorySpendingSerializer(pie_data, many=True).data,
            'bar_chart': {
                'total_income': total_income,
                'total_expenses': total_expenses,
            },
            'insight': insight,
            'transactions_count': transactions.count(),
        })


class DashboardHomeView(APIView):
    """
    Provides a consolidated summary for the user's dashboard.
    
    Includes balance, monthly income/expense totals, and recent activity.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dashboard Summary",
        description="Return high-level dashboard data: balance, income, expenses, recent activity.",
        responses=DashboardSummarySerializer
    )
    def get(self, request):
        """
        Handle GET requests for dashboard data.
        
        Returns:
            Response: Aggregated dashboard summary.
        """
        user = request.user

        income = (
            Transaction.objects.filter(user=user, type='income')
            .aggregate(Sum('amount'))['amount__sum'] or 0
        )
        expense = (
            Transaction.objects.filter(user=user, type='expense')
            .aggregate(Sum('amount'))['amount__sum'] or 0
        )

        data = {
            'user': user,
            'total_balance': income - expense,
            'monthly_income': income,
            'monthly_expenses': expense,
        }

        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)