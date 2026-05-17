"""
WSGI config for ubgraduateschool project.

WSGI (Web Server Gateway Interface) is the standard interface between
Python web applications and production web servers (e.g. gunicorn, uWSGI).

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os  # Used to set the DJANGO_SETTINGS_MODULE environment variable

from django.core.wsgi import get_wsgi_application  # Returns a WSGI-compatible callable for the project

# Tell Django which settings module to use when the WSGI server starts
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ubgraduateschool.settings')

# Create the WSGI application object that the web server calls for each request
application = get_wsgi_application()
