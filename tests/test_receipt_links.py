from datetime import date
from client.models import Client, ServiceLocation
from hr.models import Worker
from project.models import Project
from receipts.models import Receipt, PurchaseType
from travel.models import Trip


def test_receipt_links_to_trip_and_location(db):
    client = Client.objects.create(company_name="Client")
    loc = ServiceLocation.objects.create(
        client=client,
        name="Loc1",
        line1="123",
        city="Town",
        state_province="ST",
        postal_code="11111",
    )
    worker = Worker.objects.create(
        email="user@example.com",
        employee_id="E1",
        first_name="Test",
        last_name="User",
    )
    project = Project.objects.create(job_number="JOB1", name="Proj")
    project.job_num = project.job_number
    project.service_locations.add(loc)
    purchase_type = PurchaseType.objects.create(name="Meal", code="MEAL")
    trip = Trip.objects.create(
        project=project,
        traveler=worker,
        start_date=date.today(),
        end_date=date.today(),
        destination="Town",
    )
    receipt = Receipt.objects.create(
        date_of_purchase=date.today(),
        company_name="Cafe",
        project=project,
        worker=worker,
        purchase_type=purchase_type,
        total_amount=10,
        service_location=loc,
        trip=trip,
    )

    assert receipt.service_location == loc
    assert receipt.trip == trip
    assert list(loc.receipts.all()) == [receipt]
    assert list(trip.expense_receipts.all()) == [receipt]
