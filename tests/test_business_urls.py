from django.urls import reverse, resolve
from business.views import business_dashboard


def test_dashboard_url_resolves(db):
    path = reverse('business:dashboard')
    assert path == '/business/'
    assert resolve(path).func == business_dashboard
