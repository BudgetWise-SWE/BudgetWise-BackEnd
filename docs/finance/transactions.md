# Transaction Management

This module facilitates the recording and management of all financial movements within the system.

## Transaction Initialization

The system supports a simplified creation process. You can identify a category using either its numeric ID or its display name.

### Example: Creation by Category Name (Recommended)

```json
{
  "type": "expense",
  "amount": "150.00",
  "category_name": "Food",
  "description": "Weekly groceries"
}
```

### Example: Minimum Required Data

```json
{
  "type": "income",
  "amount": "5000.00",
  "category_name": "Salary"
}
```

## Data Filtering

The transaction list resource supports advanced filtering parameters, including classification (`type`), taxonomical grouping (`category`), and temporal ranges (`date_from`, `date_to`).
