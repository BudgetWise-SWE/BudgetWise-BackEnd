# System Architecture

The BudgetWise platform utilizes a modular Django architecture designed for separation of concerns, scalability, and maintainable data flows.

## Component Architecture

```mermaid
graph TD
    Client([Frontend Application]) -->|REST API| API[Django Routing & Middleware]
    
    subgraph Core Logic Layers
        API --> Auth[Accounts Module <br/> Authentication & Profiles]
        API --> Finance[Finance Module <br/> Transactions & Budgets]
        API --> Planning[Planning Module <br/> Goals & Limits]
        API --> Analytics[Analytics Module <br/> Aggregation Engine]
        API --> Notifications[Notification Module <br/> System Alerts]
    end
    
    Auth --> DB[(PostgreSQL Database)]
    Finance --> DB
    Planning --> DB
    Analytics -.-> Finance
    Notifications --> DB
```

## Technical Specification

- **Framework**: Django REST Framework (DRF)
- **Database Architecture**: PostgreSQL (hosted on Supabase)
- **Static Assets**: WhiteNoise storage management
- **Documentation Standards**: OpenAPI 3.0 via drf-spectacular
- **Deployment Architecture**: WSGI-compliant hosting via Vercel

## Project Structure

The repository is organized into distinct functional applications:

| Directory | Responsibility |
|-----------|----------------|
| `Core/` | Global project configuration and routing |
| `accounts/` | Identity management and authorization |
| `finance/` | Core ledger logic and budget management |
| `planning/` | Future-state objectives and savings targets |
| `analytics/` | Data processing for reports and insights |
| `notifications/` | Event-driven alert dispatching |
