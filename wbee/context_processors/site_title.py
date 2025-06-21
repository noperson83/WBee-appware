from django.conf import settings


def site_title(request):
    """Return site title from settings"""
    return {"SITE_TITLE": getattr(settings, "SITE_TITLE", "WBee")}
