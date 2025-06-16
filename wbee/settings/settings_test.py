from .base import *

# Use SQLite database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Limit installed apps to the bare minimum required for the todo tests
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'client.apps.ClientConfig',
    'hr.apps.HrConfig',
    'project.apps.ProjectConfig',
    'todo',
]

# Helpdesk tests require additional setup and slow down the suite. They are
# disabled for the lightweight todo test environment.
# INSTALLED_APPS.append('helpdesk.apps.HelpdeskConfig')
