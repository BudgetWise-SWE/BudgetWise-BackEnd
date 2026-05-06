# BudgetWise Backend API Documentation

Base URL: `http://localhost:8000/`

## Authentication

The backend uses Session Authentication. For frontend applications (e.g. `localhost:3000`), CORS is enabled and you must send requests with credentials.
**Important**: In your `fetch()` calls, always include `credentials: "include"`.

### Login
- **URL**: `POST /auth/login/`
- **Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "secret"
  }
  ```
- **Response**: `200 OK` with user data and a session cookie.

### Logout
- **URL**: `POST /auth/logout/`
- **Response**: `200 OK`

### Register
- **URL**: `POST /auth/`
- **Body**:
  ```json
  {
    "email": "user@example.com",
    "first_name": "First",
    "last_name": "Last",
    "password": "secret"
  }
  ```
- **Response**: `201 Created`

### Current User Profile
- **URL**: `GET /auth/me/`
- **Response**: `200 OK` with profile info (email, name, currency, language, status).

### Update Profile
- **URL**: `PATCH /auth/update_profile/`
- **Body**: (Partial updates allowed)
  ```json
  {
    "first_name": "New Name",
    "currency": "USD",
    "language": "Arabic"
  }
  ```
- **Response**: `200 OK` with updated profile.

---

## Finance Endpoints
All finance endpoints require authentication.

### Categories
- `GET /finance/categories/` - List user & predefined categories.
- `POST /finance/categories/` - Create custom category.
- `PATCH /finance/categories/{id}/` - Edit category.
- `DELETE /finance/categories/{id}/` - Delete category.

**Fields**: `name`, `type` (`expense`/`income`).

### Transactions
- `GET /finance/transactions/` - List transactions.
  - **Filters**: `?type=expense`, `?category=3`, `?date_from=2026-05-01`, `?date_to=2026-05-31`
- `POST /finance/transactions/` - Create transaction.
  - **Body (Expense)**: `{"type": "expense", "category": 3, "amount": "100", "date": "2026-05-01", "description": "Lunch"}`
  - **Body (Income)**: `{"type": "income", "amount": "1000", "source": "Job", "date": "2026-05-01"}`
- `PATCH /finance/transactions/{id}/`
- `DELETE /finance/transactions/{id}/`

### Budgets
- `GET /finance/budgets/` - List monthly budgets. (Response includes `spent` and `remaining`)
- `POST /finance/budgets/` - Create a budget.

### Budget Category Limits
- `GET /finance/budget-category-limits/` - List category limits within budgets.
- `POST /planning/budget-limit/` - Create a new limit for the *current* month.
  - **Body**: `{"category": 3, "limit": "500.00"}`

### Savings Goals
- `GET /finance/savings-goals/` - List savings goals (Response includes `progress`).
- `POST /finance/savings-goals/` - Create goal.
- `POST /finance/savings-goals/{id}/contribute/` - Add funds to goal.
  - **Body**: `{"amount": "100.00"}`

---

## Analytics Endpoints
All analytics endpoints require authentication.

### Dashboard Summary
- `GET /analytics/dashboard-summary/`
- **Response**: Returns `total_balance`, `monthly_income`, `monthly_expenses`, `recent_transactions` (array), and `budget_warnings` (array).

### Budget Alerts
- `GET /analytics/budget-alert/`
- **Response**: Returns alerts for category limits, including `progress_percentage`, `status_color`, and `alert_message`.

### Reports & Charts
- `GET /analytics/reports/` - Detailed pie/bar chart data.
  - **Filters**: `?start_date=2026-05-01&end_date=2026-05-31`
- `GET /finance/reports/monthly/` - Quick monthly totals (`?month=5&year=2026`).
- `GET /finance/reports/by_category/` - Totals grouped by category (`?month=5&year=2026`).

---

## Notifications
- `GET /notifications/notifications/` - List all notifications.
- `POST /notifications/notifications/{id}/mark_read/` - Mark one read.
- `POST /notifications/notifications/mark_all_read/` - Mark all read.
