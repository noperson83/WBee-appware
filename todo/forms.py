from django import forms
from django.contrib.auth.models import User, Group 
from django.forms import ModelForm
from todo.models import Task, TaskList
from project.models import Project, ScopeOfWork


class AddTaskListForm(ModelForm):
    """Form for creating a new :class:`TaskList`.

    ``proj`` is optional to better support generic list creation. When a
    project is supplied the scope field queryset is limited accordingly.
    """

    def __init__(self, user, proj=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].queryset = Group.objects.filter(worker=user)
        self.fields["group"].widget.attrs = {
            "id": "id_group",
            "class": "custom-select mb-3",
            "name": "group",
        }

        if proj:
            self.fields["scope"].queryset = ScopeOfWork.objects.filter(project__job_num=proj)
        else:
            self.fields["scope"].queryset = ScopeOfWork.objects.all()
        self.fields["scope"].widget.attrs = {
            "id": "id_scope",
            "class": "custom-select mb-3",
            "name": "scope",
        }
        self.fields["priority"].widget.attrs = {
            "id": "id_priority",
            "class": "custom-select mb-3",
            "name": "priority",
        }

    class Meta:
        model = TaskList
        exclude = ["created_date", "slug"]
        

class AddEditTaskForm(ModelForm):
    """The picklist showing the users to which a new task can be assigned
    must find other members of the group this TaskList is attached to."""

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        task_list = kwargs.get("initial").get("task_list")
        members = task_list.group.worker_set.all()
        self.fields["assigned_to"].queryset = members
        self.fields["assigned_to"].label_from_instance = lambda obj: "%s (%s)" % (
            obj.get_full_name(),
            obj.email,
        )
        self.fields["assigned_to"].widget.attrs = {
            "id": "id_assigned_to",
            "class": "custom-select mb-3",
            "name": "assigned_to",
        }
        self.fields["position"].widget.attrs = {
            "id": "position",
            "class": "custom-select mb-3",
            "name": "position",
        }
        self.fields["task_list"].value = kwargs["initial"]["task_list"].id

    due_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)

    title = forms.CharField(widget=forms.widgets.TextInput())

    note = forms.CharField(widget=forms.Textarea(), required=False)

    class Meta:
        model = Task
        exclude = []


class AddExternalTaskForm(ModelForm):
    """Form to allow users who are not part of the GTD system to file a ticket."""

    title = forms.CharField(widget=forms.widgets.TextInput(attrs={"size": 35}), label="Summary")
    note = forms.CharField(widget=forms.widgets.Textarea(), label="Problem Description")
    priority = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Task
        exclude = (
            "task_list",
            "created_date",
            "due_date",
            "created_by",
            "assigned_to",
            "position",
            "completed",
            "completed_date",
        )


class SearchForm(forms.Form):
    """Search."""

    q = forms.CharField(widget=forms.widgets.TextInput(attrs={"size": 35}))
