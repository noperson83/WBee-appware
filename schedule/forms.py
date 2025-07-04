from __future__ import unicode_literals

from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from schedule.models import Event, Occurrence
from django.contrib.contenttypes.models import ContentType
from django.db import models
from todo.models import Task
from schedule.widgets import ColorInput


class SpanForm(forms.ModelForm):
    start = forms.SplitDateTimeField(label=_("start"))
    end = forms.SplitDateTimeField(label=_("end"),
                                   help_text=_("The end time must be later than start time."))

    def clean(self):
        if 'end' in self.cleaned_data and 'start' in self.cleaned_data:
            if self.cleaned_data['end'] <= self.cleaned_data['start']:
                raise forms.ValidationError(_("The end time must be later than start time."))
        return self.cleaned_data


class NewEventForm(ModelForm):
    start = forms.SplitDateTimeField(label=_("start"))
    end = forms.SplitDateTimeField(label=_("end"),
                                   help_text=_("The end time must be later than start time."))
    end_recurring_period = forms.DateTimeField(
        label=_("End recurring period"),
        help_text=_("This date is ignored for one time only events."),
        required=False,
    )
    tasks = forms.ModelMultipleChoiceField(
        queryset=Task.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "custom-select mb-3"}),
        label=_("Tasks"),
    )
    related_content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(
            models.Q(app_label="travel", model="trip")
            | models.Q(app_label="receipts", model="receipt")
        ),
        required=False,
        widget=forms.HiddenInput,
    )
    related_object_id = forms.IntegerField(required=False, widget=forms.HiddenInput)

    def clean(self):
        if 'end' in self.cleaned_data and 'start' in self.cleaned_data:
            if self.cleaned_data['end'] <= self.cleaned_data['start']:
                raise forms.ValidationError(_("The end time must be later than start time."))
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        super(NewEventForm, self).__init__(*args, **kwargs)
        self.fields["project"].widget. attrs = {
            "id": "id_project",
            "class": "custom-select mb-3",
            "name": "project",
        }
        self.fields["color_event"].widget. attrs = {
            "id": "id_color_event",
            "class": "custom-select mb-3",
            "name": "color_event",
        }
        self.fields["tasks"].widget.attrs.update({
            "id": "id_tasks",
            "name": "tasks",
        })
    
    class Meta:
        model = Event
        fields = [
            'project',
            'lead',
            'workers',
            'tasks',
            'text',
            'equip',
            'details',
            'start_time',
            'start',
            'end',
            'title',
            'description',
            'creator',
            'rule',
            'end_recurring_period',
            'calendar',
            'color_event',
            'related_content_type',
            'related_object_id',
        ]
        exclude = []
        

class EventForm(SpanForm):
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
    
    end_recurring_period = forms.DateTimeField(label=_("End recurring period"),
                                               help_text=_("This date is ignored for one time only events."),
                                               required=False)

    class Meta(object):
        model = Event
        exclude = ('creator', 'created_on')


class OccurrenceForm(SpanForm):
    class Meta(object):
        model = Occurrence
        exclude = ('original_start', 'original_end', 'event', 'cancelled')


class EventAdminForm(forms.ModelForm):
    class Meta:
        exclude = []
        model = Event
        widgets = {
            'color_event': ColorInput,
        }
