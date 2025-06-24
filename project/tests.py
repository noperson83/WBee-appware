from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from .views import ProjectScheduleView
import types, sys
from unittest.mock import MagicMock

class ScheduleViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='tester@example.com', password='pass')
        self.factory = RequestFactory()

    def test_schedule_view_renders(self):
        request = self.factory.get('/schedule/')
        request.user = self.user
        dummy_event = MagicMock()
        dummy_event.objects.filter.return_value.select_related.return_value.order_by.return_value.__getitem__.return_value = []
        sys.modules['schedule.models'] = types.SimpleNamespace(Event=dummy_event)
        response = ProjectScheduleView.as_view()(request)
        self.assertEqual(response.status_code, 200)
