from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView
from django.shortcuts import get_object_or_404

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
        return initial

    def get_success_url(self):
        return self.object.get_absolute_url()


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
