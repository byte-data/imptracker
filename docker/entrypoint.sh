#!/bin/sh
set -e

python manage.py collectstatic --noinput
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py seed_defaults

exec "$@"
