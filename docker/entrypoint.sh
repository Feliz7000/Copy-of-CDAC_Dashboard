#!/bin/bash
# Docker initialization script for database setup

# Wait for postgres to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h ${POSTGRES_HOST:-localhost} -U ${POSTGRES_USER:-postgres}; do
  echo 'Waiting for postgres...'
  sleep 1
done

echo "PostgreSQL is ready!"

# Run the initialization SQL if it exists
if [ -f /docker-entrypoint-initdb.d/01-init.sql ]; then
  echo "Running initialization SQL..."
  psql -h ${POSTGRES_HOST:-localhost} -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-student_analytics} -f /docker-entrypoint-initdb.d/01-init.sql
  echo "Initialization complete!"
else
  echo "No initialization SQL found"
fi
