from business.models import BusinessType, ProjectCategory, TerminologyAlias, BusinessConfiguration
from company.models import Company
from hr.models import Worker
from wbee.context_processors.terminology import terminology


def test_business_type_and_category_creation(db):
    bt = BusinessType.objects.create(name="Lawn Care", description="test")
    cat = ProjectCategory.objects.create(business_type=bt, name="Equipment")
    assert bt.slug == "lawn-care"
    assert str(cat) == "Equipment (Lawn Care)"


def test_terminology_alias_lookup(db):
    config = BusinessConfiguration.objects.create(name="Alias Config")
    TerminologyAlias.objects.create(
        business_config=config,
        app_label="client",
        model="client",
        field="company_name",
        alias="Customer",
    )
    company = Company.objects.create(
        company_name="TestCo",
        primary_contact_name="Owner",
        business_config=config,
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
    assert data["TERMINOLOGY"]["aliases"]["client.client.company_name"] == "Customer"
