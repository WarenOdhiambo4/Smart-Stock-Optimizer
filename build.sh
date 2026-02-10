#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput

# Apply migrations normally; fall back to --fake-initial if tables already exist
python manage.py migrate --noinput || python manage.py migrate --noinput --fake-initial

python manage.py create_admin || echo "Create admin failed, continuing..."
