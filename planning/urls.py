from django.urls import path
from .views import BudgetLimitView
from .views import SavingsGoalView


urlpatterns = [

    path('budget-limit/', BudgetLimitView.as_view(), name='budget-limit'),
    path('savings-goal/', SavingsGoalView.as_view(), name='savings-goal'),
    
]