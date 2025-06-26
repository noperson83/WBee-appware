#!/bin/bash
echo "Codex Setup Starting..."
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
python manage.py migrate --noinput
python manage.py collectstatic --noinput
