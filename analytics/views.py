from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from finance.models import BudgetCategoryLimit, Transaction
from .serializers import BudgetAlertSerializer, CategorySpendingSerializer, DashboardSummarySerializer
from django.utils import timezone

class BudgetStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        active_limits = BudgetCategoryLimit.objects.filter(
            budget__user=request.user,
            budget__month=now.month,
            budget__year=now.year
        )

        serializer = BudgetAlertSerializer(active_limits, many=True)
        return Response(serializer.data)


class ReportsAnalyticsView(APIView):
    def get(self, request):
        start_date = request.query_params.get('start_date', timezone.now().date().replace(day=1))
        end_date = request.query_params.get('end_date', timezone.now().date())

        transactions = Transaction.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        )

        if not transactions.exists():
            return Response({
                "message": "No transaction data available for this period.",
                "pie_chart": [],
                "bar_chart": {},
                "insight": "Start logging your expenses to see analytics!"
            })

        total_expenses = transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 1
        spending_by_category = (
            transactions.filter(type='expense')
            .values('category__name')
            .annotate(total_spent=Sum('amount'))
        )

        pie_data = [
            {
                "category": item['category__name'],
                "total_spent": item['total_spent'],
                "percentage": round((item['total_spent'] / total_expenses) * 100, 2)
            } for item in spending_by_category
        ]

        total_income = transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0

        insight = "Your spending is 15% above average." if total_expenses > (
                    total_income * 0.9) else "Good job! You're within your budget."

        return Response({
            "pie_chart": CategorySpendingSerializer(pie_data, many=True).data,
            "bar_chart": {
                "total_income": total_income,
                "total_expenses": total_expenses
            },
            "insight": insight,
            "transactions_count": transactions.count()
        })


class DashboardHomeView(APIView):
    def get(self, request):
        user = request.user

        income = Transaction.objects.filter(user=user, type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expense = Transaction.objects.filter(user=user, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

        data = {
            'user': user,
            'total_balance': income - expense,
            'monthly_income': income,
            'monthly_expenses': expense
        }

        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)