import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wbee.settings.base")
os.environ.setdefault("SECRET_KEY", "test-secret")


def pytest_configure():
    django.setup()
