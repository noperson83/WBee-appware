from .base import *

# Use SQLite database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Ensure helpdesk app is active during tests
INSTALLED_APPS.append('helpdesk.apps.HelpdeskConfig')
