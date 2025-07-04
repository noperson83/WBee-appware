from business.models import BusinessConfiguration, TerminologyAlias
from company.models import Company
from hr.models import Worker
from wbee.context_processors.terminology import terminology


def test_terminology_alias_overrides(db):
    config = BusinessConfiguration.objects.create(name="Custom")
    TerminologyAlias.objects.create(
        business_config=config,
        app_label="client",
        model="client",
        field="company_name",
        alias="Customer Name",
    )
    company = Company.objects.create(company_name="Co", primary_contact_name="Owner", business_config=config)
    user = Worker.objects.create(
        email="u@example.com",
        employee_id="E1",
        first_name="First",
        last_name="Last",
        company=company,
    )
    request = type("Req", (), {"user": user})
    data = terminology(request)
    aliases = data["TERMINOLOGY"].get("aliases")
    assert aliases["client.client.company_name"] == "Customer Name"
