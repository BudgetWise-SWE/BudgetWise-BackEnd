# Installation and Setup

This document outlines the procedures required to initialize the BudgetWise backend environment for local development and testing.

## System Requirements

- **Python**: Version 3.10 or higher.
- **Database**: PostgreSQL (recommended) or SQLite for development purposes.
- **Environment Management**: Python virtual environments are required.

## Installation Procedure

### 1. Repository Initialization
Clone the source code and navigate to the project directory:
```bash
git clone https://github.com/your-username/BudgetWise-BackEnd.git
cd BudgetWise-BackEnd
```

### 2. Environment Configuration
Create and activate a isolated Python environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. Dependency Management
Install the required packages as specified in the requirements file:
```bash
pip install -r requirements.txt
```

### 4. Configuration
Establish a `.myenv` file in the project root with the following variables:
```env
DATABASE_URL=postgresql://user:password@host:port/dbname
DEBUG=True
SECRET_KEY=your_secret_key
```

### 5. Database Schema Initialization
Apply migrations to synchronize the database schema:
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Application Execution
Execute the development server:
```bash
python manage.py runserver
```

The application interface will be accessible at `http://localhost:8000/`.
The Administrative console is available at `http://localhost:8000/admin/`.
