"""
URL routing for the analytics application.

Defines API endpoints for high-level financial insights:
- budget-alert/: List of category spending warnings.
- dashboard-summary/: High-level overview (balance, income, expenses).
- reports/: Detailed spending breakdowns for charts.
"""
from django.urls import path
from .views import BudgetStatusView, DashboardHomeView, ReportsAnalyticsView

urlpatterns = [
    path('budget-alert/', BudgetStatusView.as_view(), name='budget-alert'),
    path('dashboard-summary/', DashboardHomeView.as_view(), name='dashboard-summary'),
    path('reports/', ReportsAnalyticsView.as_view(), name='analytics-reports'),
]