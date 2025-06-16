from django.db import models
from django.core.validators import MaxValueValidator
from django.utils.translation import gettext_lazy as _

from client.models import TimeStampedModel, UUIDModel
from project.models import Project
from hr.models import Worker


class WIPItem(UUIDModel, TimeStampedModel):
    """Generic work-in-progress tracker."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        IN_PROGRESS = "in_progress", _("In Progress")
        BLOCKED = "blocked", _("Blocked")
        COMPLETE = "complete", _("Complete")

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="wip_items",
        null=True,
        blank=True,
    )
    description = models.CharField(max_length=200)
    assigned_to = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wip_items",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    progress_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        help_text="Percent complete (0-100)",
    )
    estimated_completion = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["assigned_to"]),
        ]

    def __str__(self):
        return f"{self.project}: {self.description}" if self.project else self.description
