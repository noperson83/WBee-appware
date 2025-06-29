from django import forms
from django.forms import ModelForm
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.contrib.admin.sites import site
from django.core.exceptions import FieldDoesNotExist

from .models import Project, ScopeOfWork, ProjectMaterial, ProjectCategory


class AdminWidgetsMixin:
    """Mixin that adds admin-style add/change controls to related fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, form_field in self.fields.items():
            try:
                model_field = self._meta.model._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            rel = getattr(model_field, "remote_field", None)
            if rel:
                form_field.widget = RelatedFieldWidgetWrapper(
                    form_field.widget,
                    rel,
                    site,
                    can_add_related=True,
                    can_change_related=True,
                )


class ProjectForm(AdminWidgetsMixin, ModelForm):
    """Simplified form for creating and updating projects."""

    class Meta:
        model = Project
        fields = "__all__"


class ScopeOfWorkForm(AdminWidgetsMixin, ModelForm):
    """Basic form for scope of work items."""

    class Meta:
        model = ScopeOfWork
        fields = "__all__"


class ProjectCategoryForm(AdminWidgetsMixin, ModelForm):
    """Form for creating and editing project categories."""

    class Meta:
        model = ProjectCategory
        fields = "__all__"


class MaterialForm(AdminWidgetsMixin, ModelForm):
    """Generic form for project material items."""

    def __init__(self, proj=None, material_type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if proj:
            self.fields["project"].queryset = Project.objects.filter(job_number=proj)
        if material_type:
            self.fields["material_type"].initial = material_type

    class Meta:
        model = ProjectMaterial
        fields = "__all__"


class DeviceForm(MaterialForm):
    def __init__(self, proj=None, *args, **kwargs):
        super().__init__(proj=proj, material_type="device", *args, **kwargs)


class HardwareForm(MaterialForm):
    def __init__(self, proj=None, *args, **kwargs):
        super().__init__(proj=proj, material_type="hardware", *args, **kwargs)


class SoftwareForm(MaterialForm):
    def __init__(self, proj=None, *args, **kwargs):
        super().__init__(proj=proj, material_type="software", *args, **kwargs)


class LicenseForm(MaterialForm):
    def __init__(self, proj=None, *args, **kwargs):
        super().__init__(proj=proj, material_type="license", *args, **kwargs)


class TravelForm(MaterialForm):
    def __init__(self, proj=None, *args, **kwargs):
        super().__init__(proj=proj, material_type="travel", *args, **kwargs)


class ProjectStatusForm(AdminWidgetsMixin, ModelForm):
    """Form for updating a project's status only."""

    class Meta:
        model = Project
        fields = ["status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.instance
        if project and hasattr(project, "get_available_statuses"):
            self.fields["status"].choices = project.get_available_statuses()
