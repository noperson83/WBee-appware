from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from .views import ProjectScheduleView
from .models import Project
import types, sys
from unittest.mock import MagicMock


class ScheduleViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="tester@example.com", password="pass"
        )
        self.factory = RequestFactory()

    def test_schedule_view_renders(self):
        request = self.factory.get("/schedule/")
        request.user = self.user
        dummy_event = MagicMock()
        dummy_event.objects.filter.return_value.select_related.return_value.order_by.return_value.__getitem__.return_value = (
            []
        )
        sys.modules["schedule.models"] = types.SimpleNamespace(Event=dummy_event)
        response = ProjectScheduleView.as_view()(request)
        self.assertEqual(response.status_code, 200)


class ProjectLocationTests(TestCase):
    def test_project_multiple_locations(self):
        from location.models import BusinessCategory, Location
        from client.models import Client

        bc = BusinessCategory.objects.create(name="Test")
        client = Client.objects.create(company_name="Client")
        loc1 = Location.objects.create(
            client=client, business_category=bc, name="Site1", description="d"
        )
        loc2 = Location.objects.create(
            client=client, business_category=bc, name="Site2", description="d"
        )
        project = Project.objects.create(
            job_number="P1", name="Proj", primary_location=loc1
        )
        project.locations.add(loc1, loc2)
        self.assertEqual(project.primary_location, loc1)
        self.assertEqual(project.locations.count(), 2)


class ProjectAssetTests(TestCase):
    def test_allocated_assets_property(self):
        from location.models import BusinessCategory
        from company.models import Company
        from asset.models import Asset, AssetCategory, AssetAssignment

        bc = BusinessCategory.objects.create(name="BC")
        company = Company.objects.create(
            company_name="Co", primary_contact_name="PC", business_category=bc
        )
        category = AssetCategory.objects.create(business_category=bc, name="Tool")
        asset = Asset.objects.create(
            asset_number="A1",
            name="Asset1",
            category=category,
            asset_type="tool",
            company=company,
        )
        project = Project.objects.create(job_number="P1", name="Proj")
        AssetAssignment.objects.create(asset=asset, assigned_to_project=project)

        self.assertEqual(list(project.allocated_assets), [asset])
