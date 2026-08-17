#!/bin/sh
set -e

# Apply database migrations before starting the server
python manage.py migrate --noinput

# Run whatever command was passed (e.g. runserver)
exec "$@"