from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from finance.models import SavingsGoal
from .serializers import BudgetCategoryLimitSerializer, SavingsGoalSerializer


class BudgetLimitView(APIView):
    """Create a spending limit for a category within the current month's budget."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=BudgetCategoryLimitSerializer, responses=BudgetCategoryLimitSerializer)
    def post(self, request):
        """Accept category and limit, auto-assign to the current month's budget."""
        serializer = BudgetCategoryLimitSerializer(
            data=request.data,
            context={'request': request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Budget created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SavingsGoalView(APIView):
    """List and create savings goals for the authenticated user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SavingsGoalSerializer(many=True))
    def get(self, request):
        """Return all savings goals belonging to the authenticated user."""
        goals = SavingsGoal.objects.filter(user=request.user)
        serializer = SavingsGoalSerializer(goals, many=True)
        return Response(serializer.data)

    @extend_schema(request=SavingsGoalSerializer, responses=SavingsGoalSerializer)
    def post(self, request):
        """Create a new savings goal for the authenticated user."""
        serializer = SavingsGoalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)