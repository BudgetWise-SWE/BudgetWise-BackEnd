from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from planning.models import BudgetCategoryLimit
from .serializers import BudgetAlertSerializer, CategorySpendingSerializer, DashboardSummarySerializer
from django.utils import timezone
from finance.models import Transaction

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
        # 1. تحديد الفترة الزمنية (Default: Current Month - image_10e8d8.png)
        start_date = request.query_params.get('start_date', timezone.now().date().replace(day=1))
        end_date = request.query_params.get('end_date', timezone.now().date())

        # 2. جلب البيانات (Step 3 في Normal Scenario)
        transactions = Transaction.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        )

        # 3. هندلة الـ Exceptional Scenario (image_10e8d6.png)
        if not transactions.exists():
            return Response({
                "message": "No transaction data available for this period.",
                "pie_chart": [],
                "bar_chart": {},
                "insight": "Start logging your expenses to see analytics!"
            })

        # 4. تجهيز الـ Pie Chart (Breakdown by category - image_10e8d8.png)
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

        # 5. تجهيز الـ Bar Chart (Income vs Expenses - image_10e8d8.png)
        total_income = transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0

        # 6. الـ Key Insight (Step 5 في image_10e8d8.png)
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

        # حساب الـ Total Balance (كل الـ Income - كل الـ Expenses)
        income = Transaction.objects.filter(user=user, type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expense = Transaction.objects.filter(user=user, type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

        # تجميع البيانات للـ Serializer
        data = {
            'user': user,
            'total_balance': income - expense,
            'monthly_income': income,  # ممكن تفلترها بالشهر الحالي
            'monthly_expenses': expense
        }

        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)