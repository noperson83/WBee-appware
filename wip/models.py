from django.db import models

from client.models import TimeStampedModel, UUIDModel
from project.models import Project
from hr.models import Worker


class WIPItem(UUIDModel, TimeStampedModel):
    """Generic work-in-progress tracker."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("blocked", "Blocked"),
        ("complete", "Complete"),
    ]

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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    progress_percent = models.PositiveIntegerField(default=0)
    estimated_completion = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project}: {self.description}" if self.project else self.description

