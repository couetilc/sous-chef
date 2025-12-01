#!/usr/bin/env bash
set -euo pipefail
python manage.py migrate --noinput
cron
python manage.py crontab add
exec python manage.py runserver "${DJANGO_SERVER_IP:-localhost}:${DJANGO_SERVER_PORT:-8000}"
