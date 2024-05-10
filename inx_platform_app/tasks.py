from __future__ import absolute_import, unicode_literals
from celery import Celery, shared_task, current_task
from celery.utils.log import get_task_logger
from .models import Customer, Ke30ImportLine
import time

# app = Celery('core_app', broker='redis://localhost:6379/0')
logger = get_task_logger(__name__)


@shared_task
def task_ke30():
    model = Ke30ImportLine
    pass


@shared_task
def ticker_task(pippo):
    for iteration in range(3):
        time.sleep(7)
        logger.info("ticker_task: tick!")
    return "ticker_task completed"

@shared_task
def very_long_task():
    for number in range(50):
        time.sleep(.3)
        logger.info(f"number: {number}")
    return"task 50x completed!"

