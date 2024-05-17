web: PYTHONUNBUFFERED=1 python manage.py runserver 0.0.0.0:21013
worker: PYTHONUNBUFFERED=1 celery -A django_inx_platform worker -n localhost --loglevel=info -E
# flower: PYTHONUNBUFFERED=1 celery -A django_inx_platform flower