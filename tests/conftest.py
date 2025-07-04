import os
import django
import pytest

from business.models import BusinessConfiguration
from company.models import Company
from client.models import Client, ServiceLocation
from project.models import Project, ProjectMaterial
from material.models import MaterialLifecycle
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wbee.settings.settings_test")
os.environ.setdefault("SECRET_KEY", "test-secret")


def pytest_configure():
    django.setup()


@pytest.fixture
def business_config(db):
    return BusinessConfiguration.objects.create(name="Config")


@pytest.fixture
def company(business_config):
    return Company.objects.create(
        company_name="ACME",
        primary_contact_name="Owner",
        business_config=business_config,
    )


@pytest.fixture
def client(company):
    return Client.objects.create(company_name="ClientCo")


@pytest.fixture
def service_locations(client):
    loc1 = ServiceLocation.objects.create(
        client=client,
        name="Location A",
        line1="123 Main",
        city="Town",
        state_province="CA",
        postal_code="11111",
    )
    loc2 = ServiceLocation.objects.create(
        client=client,
        name="Location B",
        line1="456 Side",
        city="Town",
        state_province="CA",
        postal_code="22222",
    )
    return [loc1, loc2]


@pytest.fixture
def project(service_locations):
    p = Project.objects.create(job_number="JOB1", name="Test Project")
    p.service_locations.set(service_locations)
    return p


@pytest.fixture
def material_lifecycle(project):
    pm = ProjectMaterial.objects.create(project=project, material_type="device")
    return MaterialLifecycle.objects.create(
        project_material=pm,
        received_at=timezone.now(),
    )
