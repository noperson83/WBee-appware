from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import TimeCard


class TimeCardForm(forms.ModelForm):
    """Modern form for creating and editing timecards."""

    class Meta:
        model = TimeCard
        fields = [
            'date',
            'project',
            'start_time',
            'end_time',
            'lunch_start',
            'lunch_end',
            'break_minutes',
            'work_type',
            'description',
            'location',
            'mileage',
            'expenses',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'lunch_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'lunch_end': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))


TimeCardFormSet = forms.modelformset_factory(TimeCard, form=TimeCardForm, extra=1)
