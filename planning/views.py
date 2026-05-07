"""
Views for the planning application.

Provides simplified endpoints for setting quick budget limits and
managing savings goals without navigating the full finance hierarchy.
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from finance.models import SavingsGoal
from .serializers import BudgetCategoryLimitSerializer, SavingsGoalSerializer


class BudgetLimitView(APIView):
    """
    Shortcut view for creating a spending limit within the current month's budget.
    
    This view simplifies the process by auto-calculating the budget period.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Set Category Limit",
        description="Creates a spending limit for a specific category for the current month.",
        request=BudgetCategoryLimitSerializer, 
        responses=BudgetCategoryLimitSerializer
    )
    def post(self, request):
        """
        Create a new category limit.
        
        Args:
            request (Request): The HTTP request containing 'category' and 'limit'.
            
        Returns:
            Response: Success confirmation or validation errors.
        """
        serializer = BudgetCategoryLimitSerializer(
            data=request.data,
            context={'request': request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Budget created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SavingsGoalView(APIView):
    """
    View for listing and creating personal savings goals.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Savings Goals",
        description="Return all savings goals belonging to the authenticated user.",
        responses=SavingsGoalSerializer(many=True)
    )
    def get(self, request):
        """
        Fetch all goals for the user.
        
        Returns:
            Response: List of serialized savings goals.
        """
        goals = SavingsGoal.objects.filter(user=request.user)
        serializer = SavingsGoalSerializer(goals, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create Savings Goal",
        description="Initializes a new savings target for the user.",
        request=SavingsGoalSerializer, 
        responses=SavingsGoalSerializer
    )
    def post(self, request):
        """
        Create a new goal.
        
        Args:
            request (Request): The HTTP request containing goal details.
            
        Returns:
            Response: Created goal data or validation errors.
        """
        serializer = SavingsGoalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)