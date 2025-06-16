from django.urls import path

from .feeds import CalendarICalendar

app_name = "schedule"

urlpatterns = [
    path("<int:calendar_id>/ical/", CalendarICalendar(), name="calendar-ical"),
]
