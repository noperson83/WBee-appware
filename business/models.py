from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator

from client.models import TimeStampedModel


class BusinessConfiguration(TimeStampedModel):
    """Central configuration defining the type of business this deployment serves."""

    DEPLOYMENT_TYPES = [
        ("single", "Single Company"),
        ("collaborative", "Collaborative"),
        ("ecosystem", "Ecosystem"),
    ]

    BILLING_MODELS = [
        ("hourly", "Hourly Rate"),
        ("project", "Per Project"),
        ("product", "Per Product"),
        ("subscription", "Subscription"),
        ("commission", "Commission Based"),
    ]

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Detailed description of this business configuration")
    industry_details = models.TextField(blank=True, help_text="Specific industry requirements and considerations")

    # Deployment Configuration
    deployment_type = models.CharField(
        max_length=20,
        choices=DEPLOYMENT_TYPES,
        default="single",
        help_text="How this business operates (single company, collaborative, or ecosystem)"
    )
    billing_model = models.CharField(
        max_length=20,
        choices=BILLING_MODELS,
        default="project",
        help_text="Primary billing method for this business type"
    )

    # Collaboration Features
    enables_shared_inventory = models.BooleanField(
        default=False,
        help_text="Allow inventory sharing between companies"
    )
    enables_shared_workforce = models.BooleanField(
        default=False,
        help_text="Allow workforce sharing between companies"
    )
    enables_shared_clients = models.BooleanField(
        default=False,
        help_text="Allow client sharing between companies"
    )
    enables_cross_selling = models.BooleanField(
        default=False,
        help_text="Enable cross-selling between partner companies"
    )

    # Workflow and Process Requirements
    workflow_requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON configuration for business-specific workflows"
    )

    # Business Rules and Constraints
    requires_licensing = models.BooleanField(
        default=False,
        help_text="This business type requires special licensing"
    )
    requires_certifications = models.BooleanField(
        default=False,
        help_text="This business type requires certifications"
    )
    has_regulatory_compliance = models.BooleanField(
        default=False,
        help_text="This business type has regulatory compliance requirements"
    )

    # Default Settings
    default_project_duration_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Default project duration in days"
    )
    default_payment_terms_days = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text="Default payment terms in days"
    )

    # Status and Usage
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of companies using this configuration"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Business Configuration"
        verbose_name_plural = "Business Configurations"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('business:config-detail', kwargs={'slug': self.slug})

    @property
    def is_collaborative(self):
        """Check if this configuration supports collaboration"""
        return self.deployment_type in ['collaborative', 'ecosystem']

    @property
    def collaboration_features(self):
        """Get list of enabled collaboration features"""
        features = []
        if self.enables_shared_inventory:
            features.append('Shared Inventory')
        if self.enables_shared_workforce:
            features.append('Shared Workforce')
        if self.enables_shared_clients:
            features.append('Shared Clients')
        if self.enables_cross_selling:
            features.append('Cross Selling')
        return features

    def get_default_categories(self):
        """Get default project categories for this business type"""
        return self.project_categories.filter(is_active=True).order_by('order', 'name')


class BusinessType(models.Model):
    """High-level business classification (Industry verticals)."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='🏢', help_text="Emoji or icon class")
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")

    # Industry specific settings
    typical_project_size = models.CharField(
        max_length=20,
        choices=[
            ('small', 'Small (< $10K)'),
            ('medium', 'Medium ($10K - $100K)'),
            ('large', 'Large ($100K - $1M)'),
            ('enterprise', 'Enterprise (> $1M)'),
        ],
        default='medium'
    )

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")

    class Meta:
        verbose_name = "Business Type"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('business:type-detail', kwargs={'slug': self.slug})


class ProjectCategory(models.Model):
    """Category definitions per business type for project organization."""

    business_type = models.ForeignKey(
        BusinessType,
        on_delete=models.CASCADE,
        related_name='project_categories'
    )
    business_config = models.ForeignKey(
        BusinessConfiguration,
        on_delete=models.CASCADE,
        related_name='project_categories',
        null=True,
        blank=True,
        help_text="Optional: Associate with specific business configuration"
    )

    name = models.CharField(max_length=50)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='📦')
    color = models.CharField(max_length=7, default='#007bff')

    # Category Configuration
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_billable = models.BooleanField(default=True, help_text="Can items in this category be billed?")
    requires_approval = models.BooleanField(default=False, help_text="Items require approval before use")

    # Default Values
    default_unit = models.CharField(
        max_length=20,
        default='each',
        help_text="Default unit of measure (each, hour, day, etc.)"
    )
    default_markup_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Default markup percentage for this category"
    )

    class Meta:
        unique_together = [['business_type', 'slug'], ['business_config', 'slug']]
        ordering = ['order', 'name']
        verbose_name = "Project Category"
        verbose_name_plural = "Project Categories"

    def __str__(self):
        if self.business_config:
            return f"{self.name} ({self.business_config.name})"
        return f"{self.name} ({self.business_type.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BusinessTemplate(models.Model):
    """Predefined business templates for quick setup."""

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()

    # Template Configuration
    business_type = models.ForeignKey(BusinessType, on_delete=models.CASCADE)
    business_config = models.ForeignKey(
        BusinessConfiguration,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Template Metadata
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)

    # Template Data
    template_data = models.JSONField(
        default=dict,
        help_text="Complete template configuration including categories, defaults, etc."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def apply_to_company(self, company):
        """Apply this template to a company"""
        from company.models import Company

        # Update company with template configuration
        if self.business_config:
            company.business_config = self.business_config

        # Apply template data
        template_data = self.template_data

        # Create categories if they don't exist
        if 'categories' in template_data:
            for cat_data in template_data['categories']:
                ProjectCategory.objects.get_or_create(
                    business_config=self.business_config,
                    name=cat_data['name'],
                    defaults={
                        'business_type': self.business_type,
                        'icon': cat_data.get('icon', '📦'),
                        'color': cat_data.get('color', '#007bff'),
                        'is_active': True,
                    }
                )

        # Apply workflow requirements
        if 'workflow_requirements' in template_data and self.business_config:
            self.business_config.workflow_requirements.update(
                template_data['workflow_requirements']
            )
            self.business_config.save()

        company.save()

        # Increment usage count
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

        return True
