# Transaction Management

The Transaction module is the core of the BudgetWise financial engine, handling all logging and classification of financial movements.

## 🚀 Creating Transactions

We support two ways to identify categories. The new **Simplified Method** is recommended for faster frontend development.

### Method A: Simplified (Recommended)
You can identify a category by its plain-text name.

```json
{
  "type": "expense",
  "amount": "150.00",
  "category_name": "Food"
}
```

> [!TIP]
> If you provide a name that doesn't exist, the system will automatically classify it as **"Other"** to prevent data loss.

### Method B: Classic (ID-based)
Standard identification via the numeric category ID.

```json
{
  "type": "income",
  "amount": "5000.00",
  "category": 12
}
```

## 📊 Data Insights

The transaction list supports advanced filtering:
*   `type`: Filter by `expense` or `income`.
*   `category`: Filter by a specific category ID.
*   `date_from` / `date_to`: Temporal range filtering.
