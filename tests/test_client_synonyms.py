from location.models import BusinessCategory
from company.models import Company
from hr.models import Worker
from wbee.context_processors.terminology import terminology


def test_client_synonyms_in_context(db):
    bc = BusinessCategory.objects.create(
        name="Brewery",
        client_nickname="Distribution Contracts",
        client_nickname_singular="Distribution Contract",
        client_nickname_options=["Bar", "Restaurant", "Casino"],
    )
    company = Company.objects.create(
        company_name="BrewCo",
        primary_contact_name="Owner",
        business_category=bc,
    )
    user = Worker.objects.create(
        email="user@example.com",
        employee_id="E1",
        first_name="Test",
        last_name="User",
        company=company,
    )
    request = type("Req", (), {"user": user})
    data = terminology(request)
    terms = data["TERMINOLOGY"]
    assert terms["client_plural"] == "Distribution Contracts"
    assert terms["client_synonyms"] == ["Bar", "Restaurant", "Casino"]

