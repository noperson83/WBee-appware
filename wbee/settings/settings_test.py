from .base import *

# Use SQLite database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Keep the test environment lightweight by only installing apps required by the
# todo application and its dependencies. Additional apps can be added here if
# tests begin to require them.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'client.apps.ClientConfig',
    'company.apps.CompanyConfig',
    'location.apps.LocationConfig',
    'hr.apps.HrConfig',
    'project.apps.ProjectConfig',
    'material.apps.MaterialConfig',
    'todo',
]

# Enable helpdesk only when its migrations are available
# INSTALLED_APPS.append('helpdesk.apps.HelpdeskConfig')
