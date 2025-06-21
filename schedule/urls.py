from django.urls import path

from .feeds import CalendarICalendar
from . import views

app_name = "schedule"

urlpatterns = [
    path("", views.CalendarListView.as_view(), name="schedule"),
    path("calendars/", views.CalendarListView.as_view(), name="calendar_list"),
    path("<int:calendar_id>/ical/", CalendarICalendar(), name="calendar-ical"),
    path("event/create/<str:proj>/", views.EventCreateView.as_view(), name="create-event"),
    path("calendars/<slug:slug>/", views.CalendarDetailView.as_view(), name="calendar-detail"),
]
