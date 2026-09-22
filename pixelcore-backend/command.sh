#!/bin/sh
set -eu

./wait-for-it.sh db:5432
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:8000
