"""
ASGI config for ubgraduateschool project.

ASGI (Asynchronous Server Gateway Interface) is the async-capable successor
to WSGI, used by servers like Daphne or Uvicorn for WebSocket and HTTP/2 support.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os  # Used to set the DJANGO_SETTINGS_MODULE environment variable

from django.core.asgi import get_asgi_application  # Returns an ASGI-compatible callable for the project

# Tell Django which settings module to use when the ASGI server starts
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ubgraduateschool.settings')

# Create the ASGI application object that the async server calls for each request
application = get_asgi_application()
