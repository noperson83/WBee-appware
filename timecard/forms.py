from django import forms
from .models import TimeCard
from django.forms import formset_factory

class TimeCardForm(forms.Form):
    class Meta:
        model = TimeCard
        exclude = ()

TimeCardFormSet = formset_factory(form=TimeCardForm, extra=1)