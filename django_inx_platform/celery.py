from __future__ import absolute_import, unicode_literals
import os
import logging
from logging.handlers import RotatingFileHandler
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_inx_platform.settings')

app = Celery('django_inx_platform')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.broker_connection_retry_on_startup = True
app.autodiscover_tasks()

# app.conf.update(
#     CELERYD_HIJACK_ROOT_LOGGER=True,  # Add this line to output logs to stdout
# )

# Set up the logger for Celery
logger = logging.getLogger('celery')
logger.setLevel(logging.INFO)

# Configure a rotating file handler
handler = RotatingFileHandler(
    'celery_tasks.log',  # Log file path
    maxBytes=5242880,       # Maximum file size in bytes before it rotates (adjust as needed)
    backupCount=1         # Number of backup files to keep
)

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Assign logger to Celery tasks
app.log.setup(logging.INFO, logfile='celery_tasks.log')