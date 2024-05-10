celery --app django_inx_platform worker --loglevel=INFO


docker run -d --name my_redis -p 6379:6379 redis:7.2-alpine