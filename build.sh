#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

# Fix sync duplicates during deployment
python disable_sync.py disable
python fix_duplicates.py --map-only

# Bidirectional sync with Airtable
python fetch_from_airtable.py
python complete_airtable_sync.py

python disable_sync.py enable

python manage.py create_admin
python manage.py fix_user_profiles