#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating superuser if needed..."
python manage.py createsuperuser --noinput || echo "Superuser already exists"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn config.asgi:application \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
