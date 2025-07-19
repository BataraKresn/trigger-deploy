#!/bin/bash

# Initialize Flask-Migrate for the first time
# Run this script inside the backend container

echo "Initializing Flask-Migrate..."

# Set environment variables
export FLASK_APP=app.py
export PYTHONPATH=/app

# Initialize migration repository (only run once)
if [ ! -d "migrations" ]; then
    echo "Creating migrations directory..."
    flask db init
fi

# Create initial migration
echo "Creating initial migration..."
flask db migrate -m "Initial migration with all models"

# Apply migration to database
echo "Applying migration to database..."
flask db upgrade

echo "Database migrations completed successfully!"
