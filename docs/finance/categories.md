# Financial Categories

The system utilizes categories to provide a taxonomical structure for all transaction data.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/finance/categories/` | List all available categories |
| POST | `/api/finance/categories/` | Create a custom user category |
| PATCH | `/api/finance/categories/{id}/` | Update a category name |
| DELETE | `/api/finance/categories/{id}/` | Delete a custom category |

### GET Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| type | str | Filter by `expense` or `income` |

### POST Request Body

```json
{
  "name": "Groceries",
  "type": "expense"
}
```

## System Defaults

The platform seeds a standardized set of predefined categories on first access:

- **Expense**: Food, Rent, Transport, Health, Shopping, Utilities, Entertainment
- **Income**: Salary

Users can extend this taxonomy through the creation of custom, user-specific categories. Custom categories can be edited or deleted; predefined categories cannot.

## Category Types

- **expense**: Outflow transactions (default for custom categories)
- **income**: Inflow transactions
