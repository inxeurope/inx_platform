from __future__ import absolute_import, unicode_literals
from celery import Celery, shared_task
import time

app = Celery('core_app', broker='redis://localhost:6379/0')

@shared_task
def add(x, y):
    time.sleep(1)
    return f"Il risultato è: {x + y}"

@shared_task
def ticker_task():
    for iteration in range(3):
        time.sleep(2)
        print("tick!")
    return "ticker completed"

@shared_task
def very_long_task():
    for number in range(50):
        time.sleep(.3)
        print(f"number: {number}")
    return"task 50x completed!"
