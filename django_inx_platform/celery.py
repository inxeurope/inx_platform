from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_inx_platform.settings')

app = Celery('django_inx_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_connection_retry_on_startup = True
app.autodiscover_tasks()


app.conf.update(
    CELERYD_HIJACK_ROOT_LOGGER=True,  # Add this line to output logs to stdout
)