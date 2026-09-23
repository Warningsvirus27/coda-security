#!/bin/sh
set -e

echo "=== SecureCoda Backend Startup ==="

# Wait for Redis if needed
if [ -n "$REDIS_URL" ]; then
    echo "Using Redis at $REDIS_URL"
fi

# Run database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Run initial seed if database empty
echo "Checking seed data..."
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'securecoda.settings')
django.setup()
from scanner.tasks import ensure_initial_seed_data
ensure_initial_seed_data()
print('Initial seed verification complete.')
"

# Start Daphne ASGI server
echo "Starting Daphne ASGI server on 0.0.0.0:8000..."
exec daphne -b 0.0.0.0 -p 8000 securecoda.asgi:application
