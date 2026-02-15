#!/bin/bash
set -e

echo "=== EgliseConnect Production Entrypoint ==="

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! pg_isready -h ${DB_HOST:-db} -p ${DB_PORT:-5432} -U ${DB_USER:-eglise_admin} > /dev/null 2>&1; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done
echo "PostgreSQL is up!"

# Wait for Redis (with auth if password set)
echo "Waiting for Redis..."
REDIS_AUTH=""
if [ -n "${REDIS_PASSWORD}" ]; then
    REDIS_AUTH="-a ${REDIS_PASSWORD}"
fi
while ! redis-cli -h ${REDIS_HOST:-redis} ${REDIS_AUTH} ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo "Redis is up!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "=== Starting application ==="
exec "$@"
