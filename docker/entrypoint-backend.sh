#!/bin/bash
# Docker entrypoint script for Django backend

set -e

echo "=== Django Backend Container Starting ==="
echo "Django settings module: $DJANGO_SETTINGS_MODULE"
echo "Database: $POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
echo "Debug mode: $DJANGO_DEBUG"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB; do
  echo "PostgreSQL is unavailable - sleeping..."
  sleep 2
done

echo "PostgreSQL is ready!"

# Run Django management commands
echo "Running Django checks..."
python manage.py check || { echo "Django check failed!"; exit 1; }

echo "Django is configured correctly!"
echo ""
echo "=== Backend Ready ==="
echo "Run migrations: docker-compose exec backend python manage.py migrate"
echo "Create superuser: docker-compose exec backend python manage.py createsuperuser"
echo "Initialize schema: docker-compose exec backend python scripts/init_db_schema.py"
echo "Start server: docker-compose exec backend python manage.py runserver 0.0.0.0:8000"
echo ""

# Start Django development server
exec python manage.py runserver 0.0.0.0:8000
