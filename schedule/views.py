from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
import datetime

from .periods import Day, Week, Month, Year, weekday_names
from .settings import GET_EVENTS_FUNC
from .models import Event, Calendar
from .forms import NewEventForm
from project.models import Project


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Simple event creation view used in tests and examples."""

    model = Event
    form_class = NewEventForm
    template_name = "schedule/create_event.html"

    def test_func(self):
        return self.request.user.is_staff

    def get_initial(self):
        initial = super().get_initial()
        proj = self.kwargs.get("proj")
        if proj and proj != "0":
            project = Project.objects.filter(job_number=proj).first()
            if project:
                initial["project"] = project
        slug = self.kwargs.get("slug")
        if slug:
            calendar = get_object_or_404(Calendar, slug=slug)
            initial["calendar"] = calendar
        return initial

    def get_success_url(self):
        return self.object.get_absolute_url()


class EventDetailView(LoginRequiredMixin, DetailView):
    """Display detailed information for a single event."""

    model = Event
    template_name = "schedule/event.html"
    context_object_name = "event"


class CalendarDetailView(LoginRequiredMixin, DetailView):
    """Display details for a specific calendar."""

    model = Calendar
    template_name = "schedule/calendar.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "calendar"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cal = self.object
        context.update(
            {
                "calendar_name": cal.name,
                "calendar_slug": cal.slug,
                "events_count": cal.events.count(),
            }
        )
        return context


class CalendarListView(LoginRequiredMixin, ListView):
    """Simple calendar list view to serve as schedule index."""

    model = Calendar
    template_name = "schedule/calendar_list.html"
    # use default context object name "object_list" for compatibility


class MonthCalendarView(LoginRequiredMixin, DetailView):
    """Display a monthly calendar view for a specific calendar."""

    model = Calendar
    template_name = "schedule/calendar_month.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "calendar"

    def _get_date(self):
        try:
            parts = {
                key: int(self.request.GET.get(key))
                for key in ["year", "month", "day", "hour", "minute", "second"]
                if self.request.GET.get(key) is not None
            }
            if parts:
                return datetime.datetime(**parts)
        except ValueError:
            raise Http404
        return timezone.now()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar = self.object
        date = self._get_date()
        events = GET_EVENTS_FUNC(self.request, calendar)
        period = Month(events, date, tzinfo=timezone.get_current_timezone())
        context.update(
            {
                "date": date,
                "period": period,
                "calendar": calendar,
                "weekday_names": weekday_names,
            }
        )
        return context


class WeekCalendarView(LoginRequiredMixin, DetailView):
    """Display a weekly calendar view for a specific calendar."""

    model = Calendar
    template_name = "schedule/calendar_week.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "calendar"

    def _get_date(self):
        try:
            parts = {
                key: int(self.request.GET.get(key))
                for key in ["year", "month", "day", "hour", "minute", "second"]
                if self.request.GET.get(key) is not None
            }
            if parts:
                return datetime.datetime(**parts)
        except ValueError:
            raise Http404
        return timezone.now()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar = self.object
        date = self._get_date()
        events = GET_EVENTS_FUNC(self.request, calendar)
        period = Week(events, date, tzinfo=timezone.get_current_timezone())
        context.update(
            {
                "date": date,
                "period": period,
                "calendar": calendar,
                "weekday_names": weekday_names,
            }
        )
        return context


class DayCalendarView(LoginRequiredMixin, DetailView):
    """Display a daily calendar view for a specific calendar."""

    model = Calendar
    template_name = "schedule/calendar_day.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "calendar"

    def _get_date(self):
        try:
            parts = {
                key: int(self.request.GET.get(key))
                for key in ["year", "month", "day", "hour", "minute", "second"]
                if self.request.GET.get(key) is not None
            }
            if parts:
                return datetime.datetime(**parts)
        except ValueError:
            raise Http404
        return timezone.now()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar = self.object
        date = self._get_date()
        events = GET_EVENTS_FUNC(self.request, calendar)
        period = Day(events, date, tzinfo=timezone.get_current_timezone())
        context.update(
            {
                "date": date,
                "period": period,
                "calendar": calendar,
                "weekday_names": weekday_names,
            }
        )
        return context


class YearCalendarView(LoginRequiredMixin, DetailView):
    """Display a yearly calendar view for a specific calendar."""

    model = Calendar
    template_name = "schedule/calendar_year.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "calendar"

    def _get_date(self):
        try:
            parts = {
                key: int(self.request.GET.get(key))
                for key in ["year", "month", "day", "hour", "minute", "second"]
                if self.request.GET.get(key) is not None
            }
            if parts:
                return datetime.datetime(**parts)
        except ValueError:
            raise Http404
        return timezone.now()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendar = self.object
        date = self._get_date()
        events = GET_EVENTS_FUNC(self.request, calendar)
        period = Year(events, date, tzinfo=timezone.get_current_timezone())
        context.update(
            {
                "date": date,
                "period": period,
                "calendar": calendar,
                "weekday_names": weekday_names,
            }
        )
        return context


class TriMonthCalendarView(MonthCalendarView):
    """Display a three-month calendar view for a specific calendar."""

    template_name = "schedule/calendar_tri_month.html"

