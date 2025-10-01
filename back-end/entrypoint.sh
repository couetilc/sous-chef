#!/usr/bin/env bash
set -euo pipefail
python manage.py migrate --noinput
python manage.py runserver "${DJANGO_SERVER_IP:-localhost}:${DJANGO_SERVER_PORT:-8000}"
