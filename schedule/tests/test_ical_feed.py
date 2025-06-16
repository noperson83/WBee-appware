from django.test import TestCase
from django.urls import reverse
from schedule.models import Calendar


class ICalFeedTests(TestCase):
    def setUp(self):
        self.calendar = Calendar.objects.create(name="Test Calendar", slug="test")

    def test_ical_feed_returns_200(self):
        url = reverse("schedule:calendar-ical", args=[self.calendar.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/calendar")
