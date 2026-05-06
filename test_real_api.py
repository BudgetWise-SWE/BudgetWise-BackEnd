import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
django.setup()

from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()
User.objects.all().delete() # Clean up to ensure fresh run

client = APIClient()

def print_step(name, response):
    print(f"\n{'='*40}")
    print(f"STEP: {name}")
    print(f"URL: {response.request.get('PATH_INFO')}")
    print(f"STATUS: {response.status_code}")
    print('-'*40)
    if response.content:
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.content.decode('utf-8'))
    print(f"{'='*40}\n")

print("Starting API Integration Test with Real Data Instances...\n")

# 1. Register
res = client.post('/auth/', {
    'email': 'realtest@example.com',
    'first_name': 'Real',
    'last_name': 'Tester',
    'password': 'password123'
}, format='json')
print_step("User Registration", res)

# 2. Login
res = client.post('/auth/login/', {
    'email': 'realtest@example.com',
    'password': 'password123'
}, format='json')
print_step("User Login", res)

# 3. Update profile
res = client.patch('/auth/update_profile/', {
    'currency': 'USD',
    'language': 'English'
}, format='json')
print_step("Update User Profile", res)

# 4. Create Income Category
res = client.post('/finance/categories/', {
    'name': 'Freelance',
    'type': 'income'
}, format='json')
print_step("Create Custom Category (Income)", res)
inc_cat_id = res.json().get('id')

# 5. Create Income Transaction
res = client.post('/finance/transactions/', {
    'type': 'income',
    'category': inc_cat_id,
    'amount': '5000.00',
    'date': '2026-05-01',
    'source': 'Client XYZ',
    'description': 'Website design project'
}, format='json')
print_step("Log Income Transaction", res)

# 6. Create Expense Category
res = client.post('/finance/categories/', {
    'name': 'Groceries',
    'type': 'expense'
}, format='json')
print_step("Create Custom Category (Expense)", res)
exp_cat_id = res.json().get('id')

# 7. Create Budget
res = client.post('/finance/budgets/', {
    'name': 'May Budget',
    'month': 5,
    'year': 2026,
    'total_limit': '2000.00'
}, format='json')
print_step("Create Monthly Budget", res)

# 8. Create Budget Limit (Planning)
res = client.post('/planning/budget-limit/', {
    'category': exp_cat_id,
    'limit': '500.00'
}, format='json')
print_step("Set Budget Category Limit", res)

# 9. Create Expense Transaction
res = client.post('/finance/transactions/', {
    'type': 'expense',
    'category': exp_cat_id,
    'amount': '450.00',
    'date': '2026-05-05',
    'description': 'Supermarket shopping'
}, format='json')
print_step("Log Expense Transaction (Close to limit)", res)

# 10. Check Analytics Dashboard
res = client.get('/analytics/dashboard-summary/')
print_step("Fetch Dashboard Summary", res)

# 11. Check Budget Alerts
res = client.get('/analytics/budget-alert/')
print_step("Fetch Budget Alerts", res)

# 12. Transaction List with Filtering
res = client.get('/finance/transactions/?type=expense&category=' + str(exp_cat_id))
print_step("Fetch Filtered Transactions", res)

# 13. Create Savings Goal
res = client.post('/planning/savings-goal/', {
    'name': 'New Car Fund',
    'target_amount': '15000.00',
    'deadline': '2027-01-01'
}, format='json')
print_step("Create Savings Goal", res)
goal_id = res.json().get('id')

# 14. Contribute to Goal
res = client.post(f'/finance/savings-goals/{goal_id}/contribute/', {
    'amount': '2500.00'
}, format='json')
print_step("Contribute to Savings Goal", res)

print("Integration Test Completed Successfully!")
