from location.models import BusinessCategory
from project.models import ProjectCategory


def test_project_category_creation(db):
    bc = BusinessCategory.objects.create(name="Test", icon="fa-test")
    cat = ProjectCategory.objects.create(
        business_category=bc,
        name="Devices",
        icon="fa-cog",
        color="#ff0000",
        tracks_inventory=True,
        requires_scheduling=True,
        billable=True,
        workflow_stage="planning",
    )
    assert str(cat) == "Devices (Test)"
    assert cat.tracks_inventory
    assert cat.sort_order == 100
