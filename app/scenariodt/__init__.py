# Make the Celery "app" object available across the project, so that it can be used when we run tasks from the Django application instance 

from .celery import app as celery_app

__all__  = ("celery_app",)