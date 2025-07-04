from django.test import TestCase

from material.models import Supplier, MaterialLifecycle
from project.models import Project, ProjectMaterial


class MaterialLifecycleTests(TestCase):
    def test_receive_stock_creates_lifecycle(self):
        supplier = Supplier.objects.create(company_name="Acme", supplier_code="AC")
        project = Project.objects.create(job_number="P1", name="Proj")
        pm = ProjectMaterial.objects.create(project=project, material_type="device", quantity=1, unit_cost=10)

        pm.receive_stock(supplier=supplier)

        lifecycle = MaterialLifecycle.objects.get(project_material=pm)
        self.assertEqual(lifecycle.purchased_from, supplier)
        self.assertIsNotNone(lifecycle.received_at)
