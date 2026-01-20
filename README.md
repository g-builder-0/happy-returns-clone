# Happy Returns Clone - Returns Management API

A Django REST Framework API that replicates core Happy Returns functionality for processing e-commerce returns through a network of return bars.

## Purpose
This project demonstrates understanding of:
- Reverse logistics workflows
- Multi-stakeholder API design
- Complex state management in supply chain systems
- Django REST Framework architecture

## Tech Stack
- Django 5.x
- Django REST Framework 3.x
- PostgreSQL (production) / SQLite (development)
- Python 3.10+

## Setup
```bash
# Clone repository
git clone <your-repo-url>
cd happy-returns-clone

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## API Endpoints (Phase 1)
- `/api/merchants/` - Merchant CRUD
- `/api/consumers/` - Consumer CRUD
- `/api/returns/` - Return management with nested items

## Project Status
Currently implementing Phase 1: Core models and basic CRUD endpoints