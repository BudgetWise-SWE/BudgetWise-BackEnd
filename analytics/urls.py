from django.urls import path
from .views import BudgetStatusView, DashboardHomeView, ReportsAnalyticsView

urlpatterns = [
    path('budget-alert/', BudgetStatusView.as_view(), name='budget-alert'),
    path('dashboard-summary/', DashboardHomeView.as_view(), name='dashboard-summary'),
    path('reports/', ReportsAnalyticsView.as_view(), name='analytics-reports'),
]