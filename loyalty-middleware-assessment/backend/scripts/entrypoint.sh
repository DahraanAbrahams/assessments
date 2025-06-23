#!/usr/bin/env bash

# --------------------------------------------------------------------
# Entrypoint script for Django container
# --------------------------------------------------------------------
# - Waits for the database to become available
# - Applies database migrations (with retries)
# - Seeds tenant data
# - Starts the Django development server
# --------------------------------------------------------------------

# Exit immediately if any command exits with a non-zero status
set -e

# Step 1: Wait for the database to become ready
echo "Waiting for DB to be ready..."

# Number of retry attempts for database migrations
RETRIES=10

# Step 2: Run migrations with retry logic (handles race conditions with MySQL startup)
until python manage.py migrate; do
  >&2 echo "Django migration failed. Retrying in 5 seconds..."
  sleep 5
  ((RETRIES--))  # Decrement the retry counter
  if [ "$RETRIES" -le 0 ]; then
    echo "Migration failed after several attempts. Exiting."
    exit 1
  fi
done

# Step 3: Seed initial tenant data
echo "Seeding tenant data..."
python /app/seed.py

# Step 4: Start the Django development server
echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000
