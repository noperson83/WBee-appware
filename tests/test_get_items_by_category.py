from location.models import BusinessCategory
from client.models import Client, ServiceLocation
from project.models import Project, ProjectMaterial


def test_get_items_by_category(db):
    bc = BusinessCategory.objects.create(name="Test")
    client = Client.objects.create(company_name="Client")
    loc = ServiceLocation.objects.create(client=client, name="Site", line1="123", city="City", state_province="ST", postal_code="12345")
    project = Project.objects.create(job_number="P1", name="Proj")
    project.service_locations.add(loc)
    ProjectMaterial.objects.create(project=project, material_type="device", quantity=1, unit_cost=2)
    ProjectMaterial.objects.create(project=project, material_type="hardware", quantity=1, unit_cost=3)

    devices = project.get_items_by_category("device")
    assert devices.count() == 1
    assert devices.first().material_type == "device"
