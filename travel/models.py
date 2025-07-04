from django.db import models
from django.urls import reverse

from hr.models import Worker
from project.models import Project
from receipts.models import Receipt


class Trip(models.Model):
    """A work trip associated with a project and worker."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="trips",
    )
    traveler = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name="trips",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    destination = models.CharField(max_length=200)
    purpose = models.CharField(max_length=255, blank=True)
    receipts = models.ManyToManyField(Receipt, blank=True, related_name="trips")

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.traveler} - {self.destination} ({self.start_date})"

    def get_absolute_url(self):
        return reverse("travel:trip-detail", args=[str(self.id)])


class ItineraryItem(models.Model):
    """Individual item in a trip itinerary."""

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="items",
    )
    date = models.DateField()
    description = models.CharField(max_length=255)
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itinerary_items",
    )

    class Meta:
        ordering = ["date"]

    def __str__(self) -> str:
        return f"{self.date}: {self.description}"
