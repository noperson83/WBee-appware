from __future__ import unicode_literals

from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from schedule.models import Event, Occurrence
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
    end_recurring_period = forms.DateTimeField(label=_("End recurring period"),
                                               help_text=_("This date is ignored for one time only events."),
                                               required=False)

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
    
    class Meta:
        model = Event
        fields = ['project', 'lead', 'workers', 'text', 'equip', 'details', 'start_time', 'start', 'end', 'title', 'description', 'creator', 'rule', 'end_recurring_period', 'calendar', 'color_event']
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
