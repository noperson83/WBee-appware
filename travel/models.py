from django.db import models

from client.models import TimeStampedModel, UUIDModel

class Trip(UUIDModel, TimeStampedModel):
    """Simple travel record for expense tracking."""

    name = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-start_date", "name"]

    def __str__(self):
        return self.name
