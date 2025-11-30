#!/bin/sh
set -e

# If arguments are passed, run them as an ad-hoc command
# This allows: docker compose run backend python manage.py shell
if [ $# -gt 0 ]; then
    echo "Running ad-hoc command: $@"
    exec "$@"
fi

# Otherwise, run the standard startup sequence for the production server
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
