#!/bin/bash
set -e

# Install dependencies
python -m pip install -r requirements.txt

# Ensure DJANGO_SETTINGS_MODULE is set
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-wbee.settings.base}

# Use SQLite database if DATABASE_URL is not provided
export DATABASE_URL=${DATABASE_URL:-sqlite:///db.sqlite3}

# Apply database migrations
python manage.py migrate --noinput

# Collect static files (optional; uncomment if needed)
# python manage.py collectstatic --noinput
