from location.models import BusinessCategory, Location
from client.models import Client
from project.models import Project, ProjectMaterial


def test_get_items_by_category(db):
    bc = BusinessCategory.objects.create(name="Test")
    client = Client.objects.create(company_name="Client")
    loc = Location.objects.create(client=client, business_category=bc, name="Site", description="desc")
    project = Project.objects.create(job_number="P1", name="Proj", location=loc)
    ProjectMaterial.objects.create(project=project, material_type="device", quantity=1, unit_cost=2)
    ProjectMaterial.objects.create(project=project, material_type="hardware", quantity=1, unit_cost=3)

    devices = project.get_items_by_category("device")
    assert devices.count() == 1
    assert devices.first().material_type == "device"
