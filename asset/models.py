# asset/models.py - Universal Asset Management Model

from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import date, timedelta
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

# Import from your modernized apps
from client.models import TimeStampedModel, UUIDModel
from location.models import BusinessCategory, ConfigurableChoice, get_dynamic_choices
from company.models import Company, Office, Department
from hr.models import Worker, JobPosition
from project.models import Project


class Condition(models.TextChoices):
    """Normalized condition values for assets"""

    EXCELLENT = "excellent", _("Excellent")
    GOOD = "good", _("Good")
    FAIR = "fair", _("Fair")
    POOR = "poor", _("Poor")
    NEEDS_REPAIR = "needs_repair", _("Needs Repair")
    OUT_OF_SERVICE = "out_of_service", _("Out of Service")


class MaintenanceType(models.TextChoices):
    """Types of maintenance that can be performed"""

    ROUTINE = "routine", _("Routine Maintenance")
    REPAIR = "repair", _("Repair")
    INSPECTION = "inspection", _("Inspection")
    UPGRADE = "upgrade", _("Upgrade")
    CALIBRATION = "calibration", _("Calibration")


class DepreciationMethod(models.TextChoices):
    """Methods for asset depreciation"""

    STRAIGHT_LINE = "straight_line", _("Straight Line")
    DECLINING_BALANCE = "declining_balance", _("Declining Balance")
    SUM_OF_YEARS = "sum_of_years", _("Sum of Years Digits")
    UNITS_OF_PRODUCTION = "units_of_production", _("Units of Production")


class AssetCategory(TimeStampedModel):
    """Configurable asset categories for different business types"""

    business_category = models.ForeignKey(
        BusinessCategory, on_delete=models.CASCADE, related_name="asset_categories"
    )

    name = models.CharField(
        max_length=100, help_text="Vehicle, Tool, Equipment, Furniture, etc."
    )
    slug = models.SlugField(
        max_length=120, blank=True, help_text="URL friendly identifier"
    )
    description = models.TextField(
        blank=True, help_text="Description of this asset category"
    )
    icon = models.CharField(
        max_length=50, blank=True, help_text="Font Awesome icon class"
    )
    color = models.CharField(
        max_length=7, default="#007bff", help_text="Hex color code"
    )

    # Depreciation settings
    default_depreciation_years = models.PositiveIntegerField(
        default=5, help_text="Default depreciation period in years"
    )

    # Maintenance settings
    requires_maintenance = models.BooleanField(default=True)
    default_maintenance_interval_days = models.PositiveIntegerField(
        default=90, help_text="Default maintenance interval in days"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["business_category", "name"]
        unique_together = [
            ("business_category", "name"),
            ("business_category", "slug"),
        ]

    def __str__(self):
        return f"{self.name} ({self.business_category.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Asset(UUIDModel, TimeStampedModel):
    """Universal asset model for any business type"""

    # Basic identification
    asset_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique asset identifier (A001, VEH-123, etc.)",
    )

    name = models.CharField(max_length=200, help_text="Asset name/description")

    # Asset classification
    category = models.ForeignKey(
        AssetCategory, on_delete=models.CASCADE, related_name="assets"
    )

    # Dynamic asset type (configurable per business)
    asset_type = models.CharField(
        max_length=50, help_text="Specific type within category (configurable)"
    )

    # Manufacturer information
    manufacturer = models.CharField(
        max_length=100, blank=True, help_text="Manufacturer/Brand"
    )
    model = models.CharField(max_length=100, blank=True, help_text="Model number/name")
    year = models.PositiveIntegerField(
        null=True, blank=True, help_text="Year manufactured"
    )
    serial_number = models.CharField(
        max_length=100, blank=True, help_text="Serial number"
    )

    # Physical characteristics
    description = models.TextField(blank=True, help_text="Detailed description")
    specifications = models.JSONField(
        default=dict, blank=True, help_text="Technical specifications"
    )

    # Visual documentation
    primary_image = models.ImageField(
        upload_to="uploads/assets/images/%Y/%m/%d/",
        null=True,
        blank=True,
        help_text="Primary asset photo",
    )

    # Financial information
    purchase_price = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Original purchase price",
    )

    current_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Current estimated value",
    )

    # Dates
    purchase_date = models.DateField(null=True, blank=True, help_text="Date purchased")
    warranty_expiration = models.DateField(
        null=True, blank=True, help_text="Warranty expiration date"
    )

    # Ownership and assignment
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="assets",
        help_text="Company that owns this asset",
    )

    assigned_office = models.ForeignKey(
        Office,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
        help_text="Office where asset is located",
    )

    assigned_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
        help_text="Department responsible for asset",
    )

    assigned_worker = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_assets",
        help_text="Worker currently assigned this asset",
    )

    current_project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_assets",
        help_text="Project currently using this asset",
    )

    # Dynamic status and location (configurable per business)
    status = models.CharField(
        max_length=50,
        default="available",
        help_text="Asset status (configurable per business type)",
    )

    location_status = models.CharField(
        max_length=50,
        default="office",
        help_text="Physical location status (configurable)",
    )

    # Condition and maintenance
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD,
    )

    # Maintenance tracking
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    maintenance_notes = models.TextField(blank=True)

    # Usage tracking
    usage_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total usage hours (for equipment)",
    )

    mileage = models.PositiveIntegerField(
        null=True, blank=True, help_text="Current mileage (for vehicles)"
    )

    # Business-specific fields
    is_personal = models.BooleanField(
        default=False, help_text="Is this a personal asset of an employee?"
    )

    is_billable = models.BooleanField(
        default=True, help_text="Can this asset be billed to clients?"
    )

    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hourly billing rate for this asset",
    )

    # Insurance and compliance
    insurance_policy = models.CharField(max_length=100, blank=True)
    license_plate = models.CharField(
        max_length=20, blank=True, help_text="License plate (vehicles)"
    )
    registration_expiration = models.DateField(null=True, blank=True)

    # Custom fields for business-specific data
    custom_fields = models.JSONField(
        default=dict, blank=True, help_text="Custom asset data"
    )
    tags = models.JSONField(
        default=list, blank=True, help_text="Flexible tags for search and grouping"
    )

    # Status flags
    is_active = models.BooleanField(default=True)
    is_retired = models.BooleanField(default=False)

    class Meta:
        ordering = ["asset_number"]
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["assigned_worker"]),
            models.Index(fields=["current_project"]),
            models.Index(fields=["next_maintenance_date"]),
            models.Index(fields=["tags"]),
        ]

    def __str__(self):
        return f"{self.asset_number} - {self.name}"

    def get_absolute_url(self):
        return reverse("asset-detail", args=[str(self.id)])

    # Dynamic choice methods
    def get_available_statuses(self):
        """Get available statuses for this asset's business category"""
        return get_dynamic_choices("asset_status", self.category.business_category)

    def get_available_location_statuses(self):
        """Get available location statuses for this business category"""
        return get_dynamic_choices("asset_location", self.category.business_category)

    def get_available_asset_types(self):
        """Get available asset types for this category"""
        return get_dynamic_choices("asset_type", self.category.business_category)

    # Financial calculations
    @property
    def depreciated_value(self):
        """Calculate depreciated value"""
        if self.purchase_price and self.purchase_date:
            years_owned = (date.today() - self.purchase_date).days / 365.25
            depreciation_years = self.category.default_depreciation_years

            if years_owned >= depreciation_years:
                return Decimal("0.00")

            annual_depreciation = self.purchase_price / depreciation_years
            total_depreciation = annual_depreciation * Decimal(str(years_owned))

            return max(self.purchase_price - total_depreciation, Decimal("0.00"))
        return self.current_value or Decimal("0.00")

    @property
    def depreciation_rate(self):
        """Calculate annual depreciation rate"""
        if self.purchase_price and self.purchase_price > 0:
            return self.purchase_price / self.category.default_depreciation_years
        return Decimal("0.00")

    @property
    def age_in_years(self):
        """Calculate asset age in years"""
        if self.purchase_date:
            return (date.today() - self.purchase_date).days / 365.25
        return 0

    # Maintenance calculations
    @property
    def is_maintenance_due(self):
        """Check if maintenance is due"""
        if self.next_maintenance_date:
            return date.today() >= self.next_maintenance_date
        return False

    @property
    def days_until_maintenance(self):
        """Days until next maintenance"""
        if self.next_maintenance_date:
            return (self.next_maintenance_date - date.today()).days
        return None

    @property
    def is_warranty_active(self):
        """Check if warranty is still active"""
        if self.warranty_expiration:
            return date.today() <= self.warranty_expiration
        return False

    # Usage and availability
    @property
    def is_available(self):
        """Check if asset is available for use"""
        return (
            self.status == "available"
            and self.condition not in ["needs_repair", "out_of_service"]
            and self.is_active
            and not self.is_retired
        )

    @property
    def utilization_rate(self):
        """Calculate utilization rate (for billable assets)"""
        # This would need to be calculated based on actual usage data
        # Placeholder for now
        return 0

    # Maintenance management
    def schedule_next_maintenance(self):
        """Schedule next maintenance based on category defaults"""
        if self.category.requires_maintenance:
            if self.last_maintenance_date:
                base_date = self.last_maintenance_date
            else:
                base_date = self.purchase_date or date.today()

            interval = self.category.default_maintenance_interval_days
            self.next_maintenance_date = base_date + timedelta(days=interval)
            self.save()

    def mark_maintenance_complete(self, notes=""):
        """Mark maintenance as complete"""
        self.last_maintenance_date = date.today()
        if notes:
            self.maintenance_notes = notes
        self.schedule_next_maintenance()
        self.save()


class AssetMaintenanceRecord(UUIDModel, TimeStampedModel):
    """Track maintenance history for assets"""

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="maintenance_records"
    )

    maintenance_type = models.CharField(
        max_length=20,
        choices=MaintenanceType.choices,
    )

    description = models.TextField(help_text="Description of work performed")

    # Who and when
    performed_by = models.CharField(
        max_length=200, help_text="Who performed the maintenance"
    )
    performed_date = models.DateField(default=date.today)

    # Cost tracking
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    external_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Parts and materials used
    parts_used = models.JSONField(default=list, blank=True)

    # Results
    issue_resolved = models.BooleanField(default=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)

    @property
    def total_cost(self):
        return self.labor_cost + self.parts_cost + self.external_cost

    class Meta:
        ordering = ["-performed_date"]

    def __str__(self):
        return f"{self.asset.asset_number} - {self.maintenance_type} on {self.performed_date}"


class AssetAssignment(TimeStampedModel):
    """Track asset assignments over time"""

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="assignments"
    )

    # Assignment details
    assigned_to_worker = models.ForeignKey(
        Worker, on_delete=models.CASCADE, null=True, blank=True
    )

    assigned_to_project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True
    )

    assigned_to_office = models.ForeignKey(
        Office, on_delete=models.CASCADE, null=True, blank=True
    )

    # Assignment period
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)

    # Assignment details
    purpose = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)

    # Check-in/check-out
    checked_out_by = models.CharField(max_length=200, blank=True)
    checked_in_by = models.CharField(max_length=200, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["asset", "start_date"]),
        ]

    def __str__(self):
        return f"{self.asset.asset_number} assigned on {self.start_date}"


class AssetDepreciation(UUIDModel, TimeStampedModel):
    """Track depreciation schedules for assets"""

    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="depreciation_records"
    )

    # Depreciation method
    method = models.CharField(
        max_length=20,
        choices=DepreciationMethod.choices,
        default=DepreciationMethod.STRAIGHT_LINE,
    )

    # Financial details
    basis_value = models.DecimalField(max_digits=18, decimal_places=2)
    salvage_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    useful_life_years = models.PositiveIntegerField()

    # Annual depreciation amounts
    annual_depreciation = models.DecimalField(max_digits=18, decimal_places=2)
    accumulated_depreciation = models.DecimalField(
        max_digits=18, decimal_places=2, default=0
    )

    # Period
    depreciation_year = models.PositiveIntegerField()

    class Meta:
        ordering = ["asset", "depreciation_year"]
        unique_together = ["asset", "depreciation_year"]
        indexes = [
            models.Index(fields=["asset", "depreciation_year"]),
        ]

    def __str__(self):
        return f"{self.asset.asset_number} - Year {self.depreciation_year}"


# Default data creation functions
def create_default_asset_categories():
    """Create default asset categories for different business types"""

    from location.models import BusinessCategory

    # Get business categories
    try:
        construction = BusinessCategory.objects.get(name="Construction & AV")
        distribution = BusinessCategory.objects.get(name="Distribution & Logistics")
        entertainment = BusinessCategory.objects.get(name="Entertainment")
        healthcare = BusinessCategory.objects.get(name="Healthcare Services")
        food_beverage = BusinessCategory.objects.get(name="Food & Beverage")

        # Construction asset categories
        construction_assets = [
            ("Vehicles", "fas fa-truck", "#dc3545", 7, True, 90),
            ("Power Tools", "fas fa-tools", "#fd7e14", 5, True, 30),
            ("Hand Tools", "fas fa-hammer", "#6f42c1", 10, False, 365),
            ("Ladders", "fas fa-sort-up", "#20c997", 15, True, 180),
            ("Testing Equipment", "fas fa-clipboard-check", "#17a2b8", 10, True, 90),
            ("Safety Equipment", "fas fa-hard-hat", "#ffc107", 5, True, 30),
        ]

        # Distribution asset categories
        distribution_assets = [
            ("Delivery Vehicles", "fas fa-shipping-fast", "#dc3545", 7, True, 90),
            ("Warehouse Equipment", "fas fa-dolly", "#fd7e14", 10, True, 180),
            ("Loading Equipment", "fas fa-hand-truck", "#28a745", 15, True, 90),
            ("Refrigeration Units", "fas fa-snowflake", "#17a2b8", 12, True, 30),
            ("Scanning Equipment", "fas fa-barcode", "#6f42c1", 5, True, 90),
        ]

        # Entertainment asset categories
        entertainment_assets = [
            ("Sound Equipment", "fas fa-volume-up", "#e83e8c", 7, True, 30),
            ("Lighting Equipment", "fas fa-lightbulb", "#ffc107", 10, True, 60),
            ("Stage Equipment", "fas fa-theater-masks", "#6f42c1", 15, True, 180),
            ("Transport Vehicles", "fas fa-truck", "#dc3545", 7, True, 90),
            ("Instruments", "fas fa-guitar", "#fd7e14", 20, True, 365),
        ]

        # Healthcare asset categories
        healthcare_assets = [
            ("Medical Equipment", "fas fa-stethoscope", "#dc3545", 10, True, 30),
            ("Mobility Equipment", "fas fa-wheelchair", "#17a2b8", 7, True, 90),
            ("Monitoring Equipment", "fas fa-heartbeat", "#e83e8c", 8, True, 60),
            ("Transport Vehicles", "fas fa-ambulance", "#28a745", 7, True, 90),
            ("Communication Devices", "fas fa-mobile-alt", "#6f42c1", 3, True, 180),
        ]

        # Food & Beverage asset categories
        food_assets = [
            ("Kitchen Equipment", "fas fa-utensils", "#fd7e14", 10, True, 90),
            ("Refrigeration", "fas fa-snowflake", "#17a2b8", 12, True, 30),
            ("Serving Equipment", "fas fa-wine-glass", "#e83e8c", 5, True, 180),
            ("Delivery Vehicles", "fas fa-truck", "#dc3545", 7, True, 90),
            ("Cleaning Equipment", "fas fa-broom", "#28a745", 5, True, 60),
        ]

        # Create asset categories
        for category, assets in [
            (construction, construction_assets),
            (distribution, distribution_assets),
            (entertainment, entertainment_assets),
            (healthcare, healthcare_assets),
            (food_beverage, food_assets),
        ]:
            for (
                name,
                icon,
                color,
                depreciation_years,
                requires_maintenance,
                maintenance_days,
            ) in assets:
                AssetCategory.objects.get_or_create(
                    business_category=category,
                    name=name,
                    defaults={
                        "icon": icon,
                        "color": color,
                        "default_depreciation_years": depreciation_years,
                        "requires_maintenance": requires_maintenance,
                        "default_maintenance_interval_days": maintenance_days,
                    },
                )

        print("Default asset categories created successfully!")

    except BusinessCategory.DoesNotExist:
        print("Business categories not found. Please run location data creation first.")


def setup_asset_choices():
    """Setup configurable choices for asset management"""

    # Asset statuses
    asset_statuses = [
        ("available", "Available"),
        ("in_use", "In Use"),
        ("maintenance", "Under Maintenance"),
        ("repair", "Being Repaired"),
        ("retired", "Retired"),
        ("lost", "Lost/Missing"),
        ("damaged", "Damaged"),
    ]

    # Asset locations
    asset_locations = [
        ("office", "Office"),
        ("warehouse", "Warehouse"),
        ("job_site", "Job Site"),
        ("vehicle", "In Vehicle"),
        ("shop", "Repair Shop"),
        ("storage", "Storage"),
        ("field", "Field Location"),
    ]

    # Create configurable choices using the ConfigurableChoice model
    choices_to_create = [
        ("asset_status", asset_statuses),
        ("asset_location", asset_locations),
    ]

    for choice_type, values in choices_to_create:
        for index, (value, display) in enumerate(values):
            ConfigurableChoice.objects.get_or_create(
                choice_type=choice_type,
                value=value,
                defaults={
                    "display_name": display,
                    "sort_order": index * 10,
                    "applicable_to_all": True,
                },
            )

    print("Default asset choices created successfully!")
