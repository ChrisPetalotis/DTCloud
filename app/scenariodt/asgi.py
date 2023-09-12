"""
ASGI config for app project. (#? means Asynchronous Server Gateway Interface)

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scenariodt.settings')

djangp_application = get_asgi_application() # Starts the Django app and initiates uurls
from . import urls # noqa isort:skip #! This line needs to stay here to avoid an import error

application = ProtocolTypeRouter( # Checks which protocol is used to send request to server
  {
    "http": get_asgi_application(), # HTTP traffic handler
    "websocket": URLRouter(urls.websocket_urlpatterns) # Websocket traffic handler
  }
)