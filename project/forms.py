from django import forms
from django.forms import ModelForm

from .models import Project, ScopeOfWork, ProjectDevice


class ProjectForm(ModelForm):
    """Simplified form for creating and updating projects."""

    class Meta:
        model = Project
        fields = "__all__"


class ScopeOfWorkForm(ModelForm):
    """Basic form for scope of work items."""

    class Meta:
        model = ScopeOfWork
        fields = "__all__"


class DeviceForm(ModelForm):
    """Form for project device items. Optionally limits the project queryset."""

    def __init__(self, proj=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if proj:
            self.fields["project"].queryset = Project.objects.filter(job_number=proj)

    class Meta:
        model = ProjectDevice
        fields = "__all__"
