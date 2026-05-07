# Transaction Management

This module facilitates the recording and management of all financial movements within the system.

## Transaction Initialization

Example payload for transaction creation:

```json
{
  "type": "expense",
  "category": 5,
  "amount": "45.50",
  "date": "2026-05-07",
  "description": "Professional services"
}
```

## Data Filtering

The transaction list resource supports advanced filtering parameters, including classification (`type`), taxonomical grouping (`category`), and temporal ranges (`date_from`, `date_to`).
