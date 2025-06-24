from django.urls import path

from .feeds import CalendarICalendar
from . import views

app_name = "schedule"

urlpatterns = [
    path("", views.CalendarListView.as_view(), name="schedule"),
    path("calendars/", views.CalendarListView.as_view(), name="calendar_list"),
    path("<int:calendar_id>/ical/", CalendarICalendar(), name="calendar-ical"),
    path("event/create/<str:proj>/", views.EventCreateView.as_view(), name="create-event"),
    path("calendars/<slug:slug>/day/", views.DayCalendarView.as_view(), name="day_calendar"),
    path("calendars/<slug:slug>/week/", views.WeekCalendarView.as_view(), name="week_calendar"),
    path("calendars/<slug:slug>/year/", views.YearCalendarView.as_view(), name="year_calendar"),
    path("calendars/<slug:slug>/tri-month/", views.TriMonthCalendarView.as_view(), name="tri_month_calendar"),
    path("calendars/<slug:slug>/month/", views.MonthCalendarView.as_view(), name="month_calendar"),
    path("calendars/<slug:slug>/", views.CalendarDetailView.as_view(), name="calendar-detail"),
]
