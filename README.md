# BudgetWise Backend

A comprehensive Django REST API backend for personal finance management.

## Features

- **User Authentication**: Session-based authentication with Django
- **Finance Management**: Complete CRUD operations for transactions, budgets, savings goals, and categories
- **Analytics**: Generate financial reports and insights
- **Notifications**: User notifications for budget alerts and reminders
- **Planning**: Financial goals and budget planning tools

## API Endpoints

### Authentication
- `POST /auth/login/` - User login
- `POST /auth/logout/` - User logout
- `POST /auth/` - User registration

### Finance
- `GET/POST /finance/categories/` - Manage categories
- `GET/POST /finance/transactions/` - Manage transactions
- `GET /finance/transactions/summary/` - Get financial summary
- `GET /finance/transactions/by_category/` - Transactions by category
- `GET/POST /finance/budgets/` - Manage budgets
- `GET/POST /finance/savings-goals/` - Manage savings goals

### Analytics
- `GET/POST /analytics/reports/` - Generate and view reports

### Notifications
- `GET/POST /notifications/notifications/` - Manage notifications

### Planning
- `GET/POST /planning/goals/` - Manage financial goals
- `GET/POST /planning/plans/` - Manage budget plans

## Setup

1. Clone the repository
2. Create virtual environment: `python -m venv .venv`
3. Activate: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Create superuser: `python manage.py createsuperuser`
7. Run server: `python manage.py runserver`

## Testing

Run tests with: `python manage.py test`

## Documentation

See `API_DOCUMENTATION.md` for detailed API documentation.