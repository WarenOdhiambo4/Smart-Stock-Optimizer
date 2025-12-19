#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput

# Fix migration conflicts
python manage.py makemigrations --merge --noinput
python manage.py migrate

# Fix sync duplicates during deployment
python disable_sync.py disable || echo "Sync disable failed, continuing..."
python fix_duplicates.py --map-only || echo "Fix duplicates failed, continuing..."

# Bidirectional sync with Airtable
python fetch_from_airtable.py || echo "Fetch from Airtable failed, continuing..."
python complete_airtable_sync.py || echo "Sync to Airtable failed, continuing..."

python disable_sync.py enable || echo "Sync enable failed, continuing..."

python manage.py create_admin || echo "Create admin failed, continuing..."
python manage.py fix_user_profiles || echo "Fix user profiles failed, continuing..."