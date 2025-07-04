from django.contrib import admin

from .models import Trip, ItineraryItem


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["traveler", "project", "destination", "start_date", "end_date"]
    list_filter = ["start_date", "project", "traveler"]
    search_fields = ["destination", "purpose", "traveler__first_name", "traveler__last_name", "project__job_number"]


@admin.register(ItineraryItem)
class ItineraryItemAdmin(admin.ModelAdmin):
    list_display = ["trip", "date", "description", "receipt"]
    list_filter = ["trip", "date"]
    search_fields = ["description"]
