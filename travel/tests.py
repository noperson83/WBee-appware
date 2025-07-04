from django.test import TestCase
from django.utils import timezone

from hr.models import Worker
from project.models import Project
from receipts.models import Receipt, PurchaseType
from .models import Trip, ItineraryItem


class TripModelTests(TestCase):
    def setUp(self):
        self.worker = Worker.objects.create(
            email="user@example.com",
            first_name="John",
            last_name="Doe",
            employee_id="EMP001",
        )
        self.project = Project.objects.create(job_number="PRJ1", name="Test Project")
        # Some parts of the system expect a legacy job_num attribute
        self.project.job_num = self.project.job_number
        self.purchase_type = PurchaseType.objects.create(name="Flight", code="FLT")
        self.receipt = Receipt.objects.create(
            date_of_purchase=timezone.now().date(),
            company_name="Airline",
            project=self.project,
            worker=self.worker,
            purchase_type=self.purchase_type,
            total_amount=100,
        )

    def test_create_trip_and_record_expense(self):
        trip = Trip.objects.create(
            project=self.project,
            traveler=self.worker,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            destination="NYC",
            purpose="Meeting",
        )
        trip.receipts.add(self.receipt)

        item = ItineraryItem.objects.create(
            trip=trip,
            date=timezone.now().date(),
            description="Flight to NYC",
            receipt=self.receipt,
        )

        self.assertEqual(trip.receipts.count(), 1)
        self.assertEqual(trip.items.count(), 1)
        self.assertEqual(item.receipt, self.receipt)
