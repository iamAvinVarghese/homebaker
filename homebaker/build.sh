#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install python packages
pip install -r REQUIREMENTS.txt

# Collect Django static files
python manage.py collectstatic --noinput

# Run Django database migrations
python manage.py migrate
