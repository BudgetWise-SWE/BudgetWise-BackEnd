# BudgetWise BackEnd API Documentation

Base URL: `http://127.0.0.1:8000/`

## Authentication

The backend uses Django REST Framework authentication. The frontend should authenticate before calling protected finance endpoints.

### Login
- URL: `POST /auth/login/`
- Body:
  ```json
  {
    "email": "user@example.com",
    "password": "secret"
  }
  ```
- Success response:
  ```json
  {
    "message": "Login successful",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "First",
      "last_name": "Last",
      "currency": "EGP"
    }
  }
  ```
- Authentication method: session cookie by default. Use the returned session cookie for subsequent requests.

### Logout
- URL: `GET /auth/logout/`
- Requires authentication.
- Success response:
  ```json
  {
    "message": "Successfully logged out"
  }
  ```

### Register user
- URL: `POST /auth/`
- Body:
  ```json
  {
    "email": "user@example.com",
    "first_name": "First",
    "last_name": "Last",
    "password": "secret"
  }
  ```
- This creates a new user.

## Finance Endpoints
All finance endpoints require authentication.

### Categories
- URL: `GET /finance/categories/`
  - Returns predefined and user-created categories.
- URL: `POST /finance/categories/`
  - Create a custom category.
- URL: `GET /finance/categories/{id}/`
  - Retrieve category details.
- URL: `PUT /finance/categories/{id}/`
  - Update category.
- URL: `PATCH /finance/categories/{id}/`
  - Partially update category.
- URL: `DELETE /finance/categories/{id}/`
  - Delete user category.

#### Category fields
- `id`: integer
- `name`: string
- `type`: `expense` or `income`
- `parent`: integer or `null`
- `is_predefined`: boolean
- `created_at`: datetime

### Transactions
- URL: `GET /finance/transactions/`
  - List user transactions.
- URL: `POST /finance/transactions/`
  - Create a transaction.
- URL: `GET /finance/transactions/{id}/`
  - Retrieve transaction details.
- URL: `PUT /finance/transactions/{id}/`
  - Update transaction.
- URL: `PATCH /finance/transactions/{id}/`
  - Partially update transaction.
- URL: `DELETE /finance/transactions/{id}/`
  - Delete transaction.

#### Transaction fields
- `id`: integer
- `type`: `expense` or `income`
- `category`: integer or `null`
- `amount`: decimal
- `date`: `YYYY-MM-DD`
- `description`: string
- `notes`: string
- `source`: string (required for income transactions)
- `created_at`: datetime

#### Transaction examples
- Create expense:
  ```json
  {
    "type": "expense",
    "category": 3,
    "amount": 250.00,
    "date": "2026-05-01",
    "description": "Groceries",
    "notes": "Weekly market"
  }
  ```
- Create income:
  ```json
  {
    "type": "income",
    "category": 5,
    "amount": 1200.00,
    "date": "2026-05-01",
    "description": "Salary",
    "source": "Company ABC"
  }
  ```

### Transaction summaries
- URL: `GET /finance/transactions/summary/?month={month}&year={year}`
  - Returns totals for the selected period.
  - Example response:
    ```json
    {
      "income": 3000.00,
      "expense": 1800.00,
      "balance": 1200.00
    }
    ```
- URL: `GET /finance/transactions/by_category/?month={month}&year={year}`
  - Returns totals aggregated by category.
  - Example response:
    ```json
    [
      { "category_id": 3, "category_name": "Food", "total": 420.00 },
      { "category_id": 4, "category_name": "Transport", "total": 120.00 }
    ]
    ```

### Budgets
- URL: `GET /finance/budgets/`
- URL: `POST /finance/budgets/`
- URL: `GET /finance/budgets/{id}/`
- URL: `PUT /finance/budgets/{id}/`
- URL: `PATCH /finance/budgets/{id}/`
- URL: `DELETE /finance/budgets/{id}/`

#### Budget fields
- `id`: integer
- `name`: string
- `month`: integer (1-12)
- `year`: integer
- `total_limit`: decimal
- `status`: `active`, `exceeded`, or `completed`
- `created_at`: datetime
- `updated_at`: datetime

### Budget category limits
- URL: `GET /finance/budget-category-limits/`
- URL: `POST /finance/budget-category-limits/`
- URL: `GET /finance/budget-category-limits/{id}/`
- URL: `PUT /finance/budget-category-limits/{id}/`
- URL: `PATCH /finance/budget-category-limits/{id}/`
- URL: `DELETE /finance/budget-category-limits/{id}/`

#### Budget category limit fields
- `id`: integer
- `budget`: integer
- `category`: integer
- `limit`: decimal
- `spent`: decimal
- `status`: `active`, `close`, or `exceeded`

### Savings goals
- URL: `GET /finance/savings-goals/`
- URL: `POST /finance/savings-goals/`
- URL: `GET /finance/savings-goals/{id}/`
- URL: `PUT /finance/savings-goals/{id}/`
- URL: `PATCH /finance/savings-goals/{id}/`
- URL: `DELETE /finance/savings-goals/{id}/`

#### Savings goal fields
- `id`: integer
- `name`: string
- `target_amount`: decimal
- `current_amount`: decimal
- `deadline`: date or `null`
- `completed`: boolean
- `progress`: integer (0-100)
- `created_at`: datetime

## Analytics Endpoints
All analytics endpoints require authentication.

### Reports
- URL: `GET /analytics/reports/`
  - List user reports.
- URL: `POST /analytics/reports/`
  - Create a new report.
- URL: `GET /analytics/reports/{id}/`
  - Retrieve report details.
- URL: `PUT /analytics/reports/{id}/`
  - Update report.
- URL: `PATCH /analytics/reports/{id}/`
  - Partially update report.
- URL: `DELETE /analytics/reports/{id}/`
  - Delete report.

#### Report fields
- `id`: integer
- `type`: `monthly_summary`, `category_analysis`, `budget_performance`, `spending_trends`, `income_analysis`
- `title`: string
- `data`: JSON object
- `period_start`: date
- `period_end`: date
- `generated_at`: datetime

## Notifications Endpoints
All notifications endpoints require authentication.

### Notifications
- URL: `GET /notifications/notifications/`
  - List user notifications.
- URL: `POST /notifications/notifications/`
  - Create a notification.
- URL: `GET /notifications/notifications/{id}/`
  - Retrieve notification details.
- URL: `PUT /notifications/notifications/{id}/`
  - Update notification.
- URL: `PATCH /notifications/notifications/{id}/`
  - Partially update notification.
- URL: `DELETE /notifications/notifications/{id}/`
  - Delete notification.
- URL: `POST /notifications/notifications/mark_all_read/`
  - Mark all notifications as read.
- URL: `POST /notifications/notifications/{id}/mark_read/`
  - Mark specific notification as read.

#### Notification fields
- `id`: integer
- `type`: `budget_alert`, `savings_reminder`, `transaction_alert`, `goal_achievement`, `system`
- `title`: string
- `message`: string
- `is_read`: boolean
- `created_at`: datetime

## Planning Endpoints
All planning endpoints require authentication.

### Financial Goals
- URL: `GET /planning/goals/`
  - List user financial goals.
- URL: `POST /planning/goals/`
  - Create a financial goal.
- URL: `GET /planning/goals/{id}/`
  - Retrieve goal details.
- URL: `PUT /planning/goals/{id}/`
  - Update goal.
- URL: `PATCH /planning/goals/{id}/`
  - Partially update goal.
- URL: `DELETE /planning/goals/{id}/`
  - Delete goal.

#### Financial Goal fields
- `id`: integer
- `name`: string
- `description`: string
- `target_amount`: decimal
- `current_amount`: decimal
- `deadline`: date or null
- `goal_type`: `short_term`, `medium_term`, `long_term`
- `priority`: integer (1-5)
- `is_completed`: boolean
- `progress_percentage`: integer (read-only)
- `created_at`: datetime
- `updated_at`: datetime

### Budget Plans
- URL: `GET /planning/plans/`
  - List user budget plans.
- URL: `POST /planning/plans/`
  - Create a budget plan.
- URL: `GET /planning/plans/{id}/`
  - Retrieve plan details.
- URL: `PUT /planning/plans/{id}/`
  - Update plan.
- URL: `PATCH /planning/plans/{id}/`
  - Partially update plan.
- URL: `DELETE /planning/plans/{id}/`
  - Delete plan.

#### Budget Plan fields
- `id`: integer
- `name`: string
- `description`: string
- `month`: integer (1-12)
- `year`: integer
- `total_income`: decimal
- `total_expenses`: decimal
- `savings_target`: decimal
- `created_at`: datetime

## Frontend integration notes
- Always authenticate first using `/auth/login/`.
- Use the session cookie returned by Django for protected requests.
- All finance endpoints require authentication.
- For returns with lists, the response follows standard DRF paginated or unpaginated JSON format depending on configuration.

## Example frontend flow
1. `POST /auth/login/`
2. `GET /finance/categories/`
3. `GET /finance/transactions/`
4. `POST /finance/transactions/`
5. `GET /finance/reports/monthly/?month=5&year=2026`
