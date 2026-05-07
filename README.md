# BudgetWise Backend

<div align="center">
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green" alt="Django" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase" />
</div>

<br />

BudgetWise is a sophisticated financial management engine built on the Django REST Framework. It provides a scalable and secure API for comprehensive transaction tracking, budgetary constraint management, and financial data analysis.

---

## Core System Capabilities

- **Secure Identity Management**: Implementation of robust session-based authentication protocols with support for custom user profiles and global currency configurations.
- **Transaction Processing**: High-fidelity logging and taxonomical classification of financial inflows and outflows.
- **Analytical Insights**: Real-time generation of financial summaries, categorical spending distributions, and temporal trend reports.
- **Budgetary Controls**: Dynamic monthly budget allocation with category-specific spending limits and real-time status monitoring.
- **Event-Driven Notifications**: Automated dispatching of system alerts based on budgetary thresholds and financial milestones.

## System Architecture

The following diagram illustrates the high-level architecture and data flow of the BudgetWise platform:

```mermaid
graph TD
    Client([Frontend Application]) -->|REST API| API[Django Routing & Middleware]
    
    subgraph BudgetWise Core Infrastructure
        API --> Auth[Accounts Module <br/> Authentication & Profiles]
        API --> Finance[Finance Module <br/> Transactions & Budgets]
        API --> Planning[Planning Module <br/> Goals & Limits]
        API --> Analytics[Analytics Module <br/> Data Aggregation]
        API --> Notifications[Notification Module <br/> System Alerts]
    end
    
    Auth --> DB[(PostgreSQL Database <br/> Hosted on Supabase)]
    Finance --> DB
    Planning --> DB
    Analytics -.-> Finance
    Notifications --> DB
```

## Installation and Deployment

### Technical Requirements
- Python 3.10 or higher
- PostgreSQL (or SQLite for development environments)

### Setup Procedure

1. **Repository Initialization**
   ```bash
   git clone https://github.com/your-username/BudgetWise-BackEnd.git
   cd BudgetWise-BackEnd
   ```

2. **Environment Configuration**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Dependency Installation**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Establish a `.myenv` file in the project root to securely store configuration data:
   ```env
   DATABASE_URL=postgresql://user:password@host:port/dbname
   ```

5. **Schema Synchronization**
   ```bash
   python manage.py migrate
   ```

6. **Administrative Console Access (Optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Application Execution**
   ```bash
   python manage.py runserver
   ```

> [!NOTE]
> The production administrative interface is accessible at [https://budget-wise-back-end.vercel.app/admin/](https://budget-wise-back-end.vercel.app/admin/).

## API Documentation and Reference

The platform adheres to OpenAPI 3.0 specifications. Technical documentation is available through the following channels:

- **Professional Documentation Site**: [View Online Documentation](https://MuhammaddFouadd.github.io/BudgetWise-BackEnd/)
- **Production Swagger UI**: [View API Documentation](https://budget-wise-back-end.vercel.app/api/docs/)
- **ReDoc Schema**: [View ReDoc](https://budget-wise-back-end.vercel.app/api/redoc/)

## Quality Assurance

The system integrity is maintained through a comprehensive test suite. To execute automated tests:
```bash
python manage.py test
```