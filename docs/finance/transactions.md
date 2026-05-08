# Transaction Management

The Transaction module is the core of the BudgetWise financial engine, handling all logging and classification of financial movements.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/finance/transactions/` | List transactions (with filtering) |
| POST | `/api/finance/transactions/` | Create a transaction |
| PATCH | `/api/finance/transactions/{id}/` | Update a transaction |
| DELETE | `/api/finance/transactions/{id}/` | Delete a transaction |
| GET | `/api/finance/transactions/summary/` | Aggregated income/expense/balance |
| GET | `/api/finance/transactions/by_category/` | Spending totals grouped by category |

## Creating Transactions

Two methods are supported for identifying categories.

### Method A: Simplified (Recommended)

Identify a category by its plain-text name. If the name doesn't exist, the system **auto-creates** the category on the fly.

```json
{
  "type": "expense",
  "amount": "150.00",
  "category_name": "Food"
}
```

### Method B: Classic (ID-based)

Standard identification via the numeric category ID.

```json
{
  "type": "income",
  "amount": "5000.00",
  "category": 12
}
```

### Frontend Aliases

The serializer also accepts these alternative field names for frontend compatibility:

| Frontend Field | Maps To | Description |
|----------------|---------|-------------|
| `amountOfMoney` | `amount` | Transaction amount |
| `dataOfTransaction` | `date` | Transaction date |
| `name` | `description` | Transaction description |
| `"Heath"` | `"Health"` | Category name typo normalization |

## Filtering

The transaction list supports these query parameters:

| Param | Type | Description |
|-------|------|-------------|
| `type` | str | `expense`, `income`, `credit`, or `debit` |
| `category` | int/str | Category ID or name |
| `date_from` | str | Start date (YYYY-MM-DD) |
| `date_to` | str | End date (YYYY-MM-DD) |
| `search` | str | Text search in description and notes |

## Summary Endpoint

`GET /api/finance/transactions/summary/?month=5&year=2026`

Returns:
```json
{
  "total_income": 5000.00,
  "total_expenses": 3200.00,
  "total_balance": 1800.00,
  "total_transactions": 42,
  "recent_transactions": [...]
}
```

## By Category Endpoint

`GET /api/finance/transactions/by_category/?month=5&year=2026`

Returns spending totals aggregated by category, ordered by total descending.

## Budget Integration

When an expense transaction is created, the system automatically:
1. Finds the matching monthly budget and category limit
2. Increments the limit's `spent` counter
3. Recalculates both the category limit and budget statuses
