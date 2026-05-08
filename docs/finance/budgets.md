# Budgetary Controls

The system implements budgetary controls to enable users to monitor and constrain expenditures over defined periods.

## Budgets

Monthly budget containers that track total spending across all categories.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/finance/budgets/` | List all budgets for the authenticated user |
| POST | `/api/finance/budgets/` | Create a new monthly budget |

### POST Request Body

```json
{
  "name": "May 2026 Budget",
  "month": 5,
  "year": 2026,
  "total_limit": "2000.00"
}
```

The `month` field also accepts `"YYYY-MM"` string format (e.g., `"2026-05"`).

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | int | Budget ID |
| name | str | Budget display name |
| month | int | Month (1-12) |
| year | int | Year |
| total_limit | Decimal | Total spending cap |
| spent | Decimal | Computed total expenses for this period (read-only) |
| remaining | Decimal | `total_limit - spent` (read-only) |
| status | str | `active`, `exceeded`, or `completed` |

### Budget Status

- **Active**: Total spending is within the budget limit
- **Exceeded**: Total spending has surpassed the limit
- **Completed**: Total spending exactly equals the limit

---

## Budget Category Limits

Per-category spending caps within a monthly budget. Creating a limit for an existing budget+category pair **updates** the existing limit (upsert behavior) instead of returning a duplicate error.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/finance/budget-category-limits/` | List all category limits |
| POST | `/api/finance/budget-category-limits/` | Create or update a category limit |
| PATCH | `/api/finance/budget-category-limits/{id}/` | Partially update a limit |
| DELETE | `/api/finance/budget-category-limits/{id}/` | Delete a limit |

An alias is also registered:
- `GET /api/finance/budget-category-list/`

### GET Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| month | str | Filter by month in `YYYY-MM` format |

### POST Request Body

```json
{
  "budget": 1,
  "category": 5,
  "limit": "500.00",
  "month": "2026-05"
}
```

- `budget` and `category` are integer IDs
- `month` is write-only, consumed during validation
- If `category` is omitted, `category_name` (string) can be provided instead for text-based resolution
- If `budget` is omitted, one will be auto-created for the given `month`

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | int | Limit ID |
| budget | int | Parent budget ID |
| category | str | Category **name** (not ID) for frontend display |
| limit | Decimal | Spending cap |
| spent | Decimal | Real-time spent computed from transactions |
| remaining | Decimal | `max(limit - spent, 0)` |
| status | str | `active`, `close`, or `exceeded` |

### Category Limit Status

- **Active**: Spending is below 90% of the limit
- **Close**: Spending has reached 90-100% of the limit
- **Exceeded**: Spending has surpassed the limit

---

## Data Flow

1. Expense transactions are created via `/api/finance/transactions/`
2. `TransactionService` calls `BudgetService.process_expense()`
3. The service finds the matching budget and category limit
4. The limit's `spent` field (DB-persisted) is incremented
5. Both the category limit and parent budget statuses are recalculated

The serializer's `get_spent` method provides a real-time spent calculation by aggregating expense transactions, cached per-instance to avoid redundant queries.
