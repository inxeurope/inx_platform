# from __future__ import absolute_import, unicode_literals
from celery import Celery, shared_task, current_task
from celery.utils.log import get_task_logger
from .models import Customer, Ke30ImportLine
import time
import os

# app = Celery('core_app', broker='redis://localhost:6379/0')
logger = get_task_logger(__name__)


@shared_task
def task_ke30(file, id_of_UploadedFile, user_email):
    # Get the task id
    task_id = current_task.request.id
    # Setting the model we will use to insert lines
    model = Ke30ImportLine
    file_path = file.file_path + "/" + file.file_name
    if not os.path.exists(file_path):
        logger.info(f"task id: {task_id} - {user_email} - {file_path}")
        logger.error(f"File does not exist.")
        return
    logger.info(f"the file {file_path} has been found")
    


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

