#!/bin/sh
set -e

# Apply database migrations before starting the server
python manage.py migrate --noinput

# Create a superuser automatically from environment variables (idempotent)
python manage.py shell <<EOF
import os
from django.contrib.auth import get_user_model
User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpassword')
if not User.objects.filter(email=email).exists():
    print(f"Creating superuser '{email}'...")
    User.objects.create_superuser(email=email, password=password)
    print(f"Superuser '{email}' created.")
else:
    print(f"Superuser '{email}' already exists.")
EOF

# Run whatever command was passed (e.g. runserver)
exec "$@"