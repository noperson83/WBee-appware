from django.db import models
from django.utils.text import slugify

from client.models import TimeStampedModel


class BusinessConfiguration(TimeStampedModel):
    """Central configuration defining the type of business this deployment serves."""

    DEPLOYMENT_TYPES = [
        ("single", "Single Company"),
        ("collaborative", "Collaborative"),
        ("ecosystem", "Ecosystem"),
    ]

    BILLING_MODELS = [
        ("hourly", "Hourly"),
        ("project", "Per Project"),
        ("product", "Per Product"),
    ]

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    industry_details = models.TextField(blank=True)

    deployment_type = models.CharField(max_length=20, choices=DEPLOYMENT_TYPES, default="single")
    billing_model = models.CharField(max_length=20, choices=BILLING_MODELS, default="project")

    enables_shared_inventory = models.BooleanField(default=False)
    enables_shared_workforce = models.BooleanField(default=False)
    enables_shared_clients = models.BooleanField(default=False)
    enables_cross_selling = models.BooleanField(default=False)

    workflow_requirements = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BusinessType(models.Model):
    """High-level business classification."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = "Business Type"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProjectCategory(models.Model):
    """Category definitions per business type."""
    business_type = models.ForeignKey(BusinessType, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    slug = models.SlugField()
    icon = models.CharField(max_length=50, default='📦')
    color = models.CharField(max_length=7, default='#007bff')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['business_type', 'slug']
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.business_type.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

