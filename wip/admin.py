from django.contrib import admin
from .models import WIPItem

@admin.register(WIPItem)
class WIPItemAdmin(admin.ModelAdmin):
    list_display = ("description", "project", "assigned_to", "status", "progress_percent", "estimated_completion")
    list_filter = ("status", "project")
    search_fields = ("description", "project__name", "assigned_to__first_name", "assigned_to__last_name")

