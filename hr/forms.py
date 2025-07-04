from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import Worker

# Standard role options used across the admin. Keeping this list here
# allows the forms and the admin interface to share the same choices.
ROLE_CHOICES = [
    ("admin", "Admin"),
    ("staff", "Staff"),
    ("supervisor", "Supervisor"),
    ("project_manager", "Project Manager"),
    ("employee", "Employee"),
    ("client", "Client"),
    ("accountant", "Accountant"),
    ("owner", "Owner"),
]

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput, required=False)
    # Present roles as a set of checkboxes for easier selection
    roles = forms.MultipleChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Worker
        fields = [
            'email', 'first_name', 'last_name', 'middle_name', 'preferred_name',
            'phone_number', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'date_of_birth', 'gender',
            'position', 'office', 'department', 'manager', 'employment_status',
            'date_of_hire', 'current_hourly_rate', 'current_annual_salary',
            'bio', 'skills', 'profile_picture', 'resume', 'roles',
            'groups', 'user_permissions', 'is_active', 'is_staff', 'is_admin',
            'is_superuser'
        ]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = Worker.objects.filter(email=email)
        if qs.exists():
            raise forms.ValidationError("email is taken")
        return email

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2


class WorkerAdminCreationForm(forms.ModelForm):
    """A form for creating new Workers. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
    roles = forms.MultipleChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Worker
        fields = ('email',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        worker = super(WorkerAdminCreationForm, self).save(commit=False)
        worker.set_password(self.cleaned_data["password1"])
        if commit:
            worker.save()
        return worker


class WorkerAdminChangeForm(forms.ModelForm):
    """A form for updating Workers. Includes all the fields on
    the Worker, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Worker
        fields = ('email', 'password')

    def clean_password(self):
        # Regardless of what the Worker provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]
