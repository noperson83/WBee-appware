import datetime
from receipts.models import Receipt, PurchaseType
from client.models import Client, ServiceLocation
from project.models import Project
from hr.models import Worker
from travel.models import Trip


def test_receipt_links(db):
    client = Client.objects.create(company_name="Client")
    loc = ServiceLocation.objects.create(
        client=client,
        name="Site",
        line1="123",
        city="City",
        state_province="ST",
        postal_code="12345",
    )
    project = Project.objects.create(job_number="P1", name="Proj")
    project.job_num = project.job_number  # compatibility with Receipt.__str__
    worker = Worker.objects.create(
        email="w@example.com",
        employee_id="E1",
        first_name="W",
        last_name="Worker",
    )
    ptype = PurchaseType.objects.create(name="Meals", code="ME")
    trip = Trip.objects.create(name="Trip 1")

    receipt = Receipt.objects.create(
        date_of_purchase=datetime.date.today(),
        company_name="Vendor",
        project=project,
        worker=worker,
        purchase_type=ptype,
        total_amount=10,
        service_location=loc,
        trip=trip,
    )

    assert receipt.service_location == loc
    assert receipt.trip == trip
