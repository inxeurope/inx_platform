web: python manage.py runserver | sed $'s/^/\\033[34m/g' | sed $'s/$/\\033[0m/g'
worker: celery -A django_inx_platform worker --loglevel=info | sed $'s/^/\\033[32m/g' | sed $'s/$/\\033[0m/g'
