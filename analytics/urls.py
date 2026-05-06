from django.urls import path
from .views import BudgetStatusView
from .views import DashboardHomeView

urlpatterns = [

    path('budget-alert/', BudgetStatusView.as_view(), name='budget-alert'),
    path('dashboard-summary/', DashboardHomeView.as_view(), name='dashboard-summary'),

]