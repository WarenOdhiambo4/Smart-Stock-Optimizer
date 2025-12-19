#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py sync_all_from_airtable
python manage.py create_admin
python manage.py fix_user_profiles