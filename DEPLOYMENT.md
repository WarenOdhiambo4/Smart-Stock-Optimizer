# 🚀 Kabisa ERP - Render Deployment Guide

## Environment Variables for Render

Set these in your Render dashboard:

```
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here
DEBUG=False
PYTHON_VERSION=3.11.0
```

## Render Settings

- **Build Command:** `./build.sh`
- **Start Command:** `gunicorn saas_project.wsgi:application`
- **Python Version:** 3.11.0

## Admin Access

- **URL:** `https://your-app.onrender.com/admin/users/`
- **Username:** `admin`
- **Email:** `odhiambowaren89@gmail.com`
- **Password:** `0790018750..`

## Features Working

✅ Multi-branch ERP system
✅ Airtable cloud database (permanent storage)
✅ User management with email validation
✅ Auto-sync to Airtable
✅ Inventory, Sales, Orders, Logistics tracking

## Your Airtable Base

- **Base ID:** `appoh0qpPOqZOH35E`
- **All 15 tables created with proper relationships**
- **Data syncs automatically from Django to Airtable**