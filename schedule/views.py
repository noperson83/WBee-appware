from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import CreateView
from django.shortcuts import get_object_or_404

from .models import Event
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
