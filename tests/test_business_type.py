from business.models import BusinessType, ProjectCategory


def test_business_type_and_category_creation(db):
    bt = BusinessType.objects.create(name="Lawn Care", description="test")
    cat = ProjectCategory.objects.create(business_type=bt, name="Equipment")
    assert bt.slug == "lawn-care"
    assert str(cat) == "Equipment (Lawn Care)"
