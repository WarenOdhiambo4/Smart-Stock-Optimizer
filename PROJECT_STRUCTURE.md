# 📁 Kabisa ERP - Project Structure

## Core Files

```
├── core/                          # Main Django app
│   ├── models.py                  # Database models (Branch, Product, Sale, etc.)
│   ├── views.py                   # Web interface views
│   ├── admin_views.py             # Admin user management
│   ├── admin_airtable.py          # User creation with email validation
│   ├── airtable_service.py        # Airtable API connection
│   ├── airtable_adapter.py        # Django ↔ Airtable sync
│   ├── signals.py                 # Auto-sync to Airtable on save
│   └── management/commands/       # Custom Django commands
│       └── sync_airtable.py       # Manual sync command
│
├── templates/                     # HTML templates
│   └── admin/user_management.html # User creation interface
│
├── saas_project/                  # Django project settings
│   ├── settings.py                # Main configuration
│   └── urls.py                    # URL routing
│
├── .env                          # Environment variables (local)
├── requirements.txt              # Python dependencies
├── build.sh                     # Render build script
├── render.yaml                  # Render deployment config
└── manage.py                    # Django management
```

## Key Components

### 🔄 Auto-Sync System
- **signals.py** - Automatically syncs new data to Airtable
- **airtable_adapter.py** - Handles Django ↔ Airtable conversion
- **airtable_service.py** - Direct Airtable API calls

### 👥 User Management
- **admin_airtable.py** - Creates users with email validation
- **admin_views.py** - Web interface for user creation
- **Email validation** - Checks if email exists using DNS

### 📊 Database Models
- **Branch** - Company locations
- **Product** - Inventory items
- **Sale** - Customer transactions
- **Order** - Purchase orders
- **Employee** - Staff management
- **Vehicle** - Fleet tracking
- **Trip** - Logistics operations

## How It Works

1. **Create data in Django** → Auto-syncs to Airtable
2. **Airtable stores permanently** → Survives deployments
3. **Admin creates users** → Email validated, passwords generated
4. **All business data** → Backed up in cloud (Airtable)