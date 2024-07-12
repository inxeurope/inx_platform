from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_inx_platform.settings')

app = Celery('django_inx_platform')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.broker_connection_retry_on_startup = True
app.autodiscover_tasks()

app.conf.update(
    CELERYD_HIJACK_ROOT_LOGGER=True,  # Add this line to output logs to stdout
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')