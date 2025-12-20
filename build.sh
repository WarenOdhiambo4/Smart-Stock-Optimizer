#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput

# Fix migration conflicts first
python manage.py fix_migrations || echo "Fix migrations failed, continuing..."
python manage.py migrate --fake-initial || echo "Fake initial failed, trying normal migrate..."
python manage.py migrate

python manage.py create_admin || echo "Create admin failed, continuing..."