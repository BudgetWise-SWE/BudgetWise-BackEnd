from rest_framework.permissions import IsAuthenticated
from .serializers import BudgetCategoryLimitSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SavingsGoal
from .serializers import SavingsGoalSerializer

class BudgetLimitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Normal Scenario: استلام البيانات[cite: 2]
        serializer = BudgetCategoryLimitSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Budget created successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SavingsGoalView(APIView):
    def get(self, request):
        # عرض الأهداف الخاصة بالمستخدم الحالي فقط
        goals = SavingsGoal.objects.filter(user=request.user)
        serializer = SavingsGoalSerializer(goals, many=True)
        return Response(serializer.data)

    def post(self, request):
        # إنشاء هدف جديد (Normal Scenario)[cite: 2]
        serializer = SavingsGoalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)