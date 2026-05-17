#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os   # Provides access to operating system environment variables
import sys  # Provides access to command-line arguments passed to the script


def main():
    """Run administrative tasks."""
    # Set the default Django settings module so manage.py knows which settings file to use
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ubgraduateschool.settings')
    try:
        # Import Django's management command runner
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Raise a helpful error if Django is not installed or the virtualenv is not active
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Execute the management command passed via the command line (e.g. runserver, migrate)
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # Only run main() when this file is executed directly (not imported)
    main()
