from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from decimal import Decimal
from schedule.models import Calendar, Event
from receipts.models import Receipt, PurchaseType
from hr.models import Worker
from company.models import Company


class EventGenericRelationTests(TestCase):
    def setUp(self):
        company = Company.objects.create(company_name="Co")
        self.user = Worker.objects.create_superuser(
            email="admin@example.com",
            password="pass",
            first_name="A",
            last_name="B",
            employee_id="E1",
            company=company,
        )
        self.calendar = Calendar.objects.create(
            name="Cal", slug="cal", owner=self.user
        )
        self.purchase_type = PurchaseType.objects.create(name="Travel", code="TR")
        self.receipt = Receipt.objects.create(
            date_of_purchase=timezone.now().date(),
            company_name="Co",
            worker=self.user,
            purchase_type=self.purchase_type,
            total_amount=Decimal("10.00"),
        )
        self.client.force_login(self.user)

    def test_create_event_links_receipt(self):
        ct = ContentType.objects.get_for_model(Receipt)


        start = timezone.now()
        end = start + timezone.timedelta(hours=1)
        event = Event.objects.create(
            title="Receipt Event",
            start=start,
            end=end,
            calendar=self.calendar,
            creator=self.user,
            related_content_type=ct,
            related_object_id=self.receipt.pk,
        )
        self.assertEqual(event.related_object, self.receipt)
