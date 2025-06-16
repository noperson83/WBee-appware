from django.contrib import admin

from .models import WIPItem


@admin.register(WIPItem)
class WIPItemAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "project",
        "assigned_to",
        "status",
        "progress_percent",
    )
    list_filter = ("status", "project")
    search_fields = ("description",)

