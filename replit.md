# SaasApp - Inventory & Sales Management System

## Overview
A Django-based SaaS application for multi-branch inventory and sales management. Built with PostgreSQL database for reliable data storage.

## Project Structure
```
/
├── saas_project/          # Django project settings
│   ├── settings.py        # Main configuration
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI application
├── core/                  # Main application
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── urls.py            # App URL patterns
│   └── admin.py           # Admin configuration
├── templates/             # HTML templates
│   ├── base.html          # Base template with navbar
│   └── core/              # App-specific templates
├── static/
│   └── css/style.css      # Custom styles
└── manage.py              # Django management script
```

## Database Models
- **Branch**: Multi-branch support with many-to-many employee relationship
- **Employee**: Staff members who can work across multiple branches
- **Product**: Product catalog with SKU, pricing, and categories
- **Stock**: Branch-specific inventory with low-stock alerts
- **StockMovement**: Track all stock changes including inter-branch transfers
- **Order**: Purchase orders that add stock when completed
- **OrderItem**: Line items that auto-create products if needed
- **Sale**: Sales transactions that reduce stock
- **SaleItem**: Sale line items linked to stock

## Key Features
- Dashboard with key metrics and alerts
- Branch and employee management
- Product catalog management
- Stock tracking per branch with low-stock warnings
- Inter-branch stock transfers with approval workflow
- Purchase orders that increase stock on completion
- Sales that automatically reduce stock
- Clean UI with fixed top navbar, Nunito font, compact design

## Running the Application
```bash
python manage.py runserver 0.0.0.0:5000
```

## User Preferences
- No sidebar - top fixed navbar only
- Small fonts (Nunito)
- Small buttons and search boxes
- Clean, minimal UI design

## Recent Changes
- Initial setup with all database models
- Created all CRUD views for branches, employees, products
- Implemented stock management with transfer workflow
- Added order and sales functionality
- Designed clean UI with Bootstrap 5

## Environment Variables
- DATABASE_URL, PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE (PostgreSQL)
- SESSION_SECRET (Django secret key)
