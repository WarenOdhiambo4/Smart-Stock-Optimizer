#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate

# Fix sync duplicates during deployment
python disable_sync.py disable
python fix_duplicates.py --map-only
python disable_sync.py enable

python manage.py sync_all_from_airtable
python manage.py create_admin
python manage.py fix_user_profiles