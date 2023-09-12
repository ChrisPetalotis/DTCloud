import os
from celery import Celery

# Initiate the Django settings module  to allow for Celery to access the settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scenariodt.settings')
app = Celery('scenariodt')

# Instruct Celery on how to access the Django settings
# Look only for variables starting with "CELERY_"
app.config_from_object("django.conf:settings", namespace="CELERY")

# Whenever a new task is created in Celery, it needs to get registered that task to Celery
# @app.task # Registers task with Celery
# def new_task():
#   return

app.autodiscover_tasks() # Looks for tasks in the tasks.py file in the project and in all the installed apps