from django.test import TestCase

from .models import Asset, AssetCategory, AssetAssignment
from project.models import Project
from location.models import BusinessCategory
from company.models import Company


class AssetAssignmentTests(TestCase):
    def setUp(self):
        self.bc = BusinessCategory.objects.create(name="Test")
        self.company = Company.objects.create(
            company_name="Co", primary_contact_name="PC", business_category=self.bc
        )
        self.category = AssetCategory.objects.create(
            business_category=self.bc, name="Tool"
        )
        self.asset = Asset.objects.create(
            asset_number="A1",
            name="Asset1",
            category=self.category,
            asset_type="tool",
            company=self.company,
        )
        self.project = Project.objects.create(job_number="P1", name="Proj1")

    def test_asset_assignment_m2m(self):
        AssetAssignment.objects.create(
            asset=self.asset, assigned_to_project=self.project, status="active"
        )

        self.assertIn(self.project, self.asset.projects.all())
        self.assertIn(self.asset, self.project.assets.all())
