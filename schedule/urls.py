from django.urls import path

from .feeds import CalendarICalendar
from . import views

app_name = "schedule"

urlpatterns = [
    path("<int:calendar_id>/ical/", CalendarICalendar(), name="calendar-ical"),
    path("event/create/<str:proj>/", views.EventCreateView.as_view(), name="create-event"),
]
