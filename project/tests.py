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
