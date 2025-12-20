#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput

# Mark all migrations as applied since tables already exist
python manage.py migrate --fake

python manage.py create_admin || echo "Create admin failed, continuing..."