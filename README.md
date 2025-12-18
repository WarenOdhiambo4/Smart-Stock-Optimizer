# 🏢 Kabisa Enterprise ERP System

**Complete business management system with cloud database integration**

## 🚀 Quick Start

1. **Local Development:**
   ```bash
   python manage.py runserver
   ```
   Access: `http://127.0.0.1:8000`

2. **Admin Panel:**
   - URL: `/admin/users/`
   - Username: `admin`
   - Create users with email validation

## 📋 Features

✅ Multi-branch operations
✅ Inventory & stock management  
✅ Sales & order tracking
✅ Fleet & logistics management
✅ Financial expense tracking
✅ User management with roles
✅ **Airtable cloud database** (permanent storage)
✅ **Auto-sync** - Data never lost

## 📚 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Render deployment guide
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Code organization

## 🔧 Tech Stack

- **Backend:** Django 6.0, Python 3.11
- **Database:** Airtable (cloud) + SQLite (local)
- **Deployment:** Render
- **Email Validation:** DNS lookup verification