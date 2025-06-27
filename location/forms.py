from django import forms
from django.contrib.auth.models import User, Group
from django.forms import ModelForm, inlineformset_factory, modelformset_factory
from django.core.exceptions import ValidationError

from client.models import Client, Address, Contact
from .models import Location, BusinessCategory, LocationType, LocationDocument, LocationNote, get_dynamic_choices


class LocationForm(ModelForm):
    """Modern form for creating/updating locations"""
    
    class Meta:
        model = Location
        fields = [
            'name', 'client', 'business_category', 'location_type',
            'description', 'scope_summary', 'profile_image',
            'location_category', 'latitude', 'longitude',
            'google_maps_url', 'google_plus_code', 'status',
            'first_contact_date', 'site_survey_date', 'contract_signed_date',
            'project_start_date', 'estimated_completion',
            'facility_size', 'facility_size_unit', 'capacity',
            'existing_systems', 'access_requirements', 'work_hours',
            'special_requirements', 'emergency_contact_info',
            'parking_available', 'loading_access', 'storage_available',
            'custom_fields'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location name'
            }),
            'client': forms.Select(attrs={
                'class': 'form-control'
            }),
            'business_category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_business_category'
            }),
            'location_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_location_type'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed location description'
            }),
            'scope_summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'High-level scope overview'
            }),
            'profile_image': forms.ClearableFileInput(attrs={
                'class': 'form-control-file'
            }),
            'location_category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Urban, Rural, Indoor, Outdoor, etc.'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': '40.7128'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': '-74.0060'
            }),
            'google_maps_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://goo.gl/maps/...'
            }),
            'google_plus_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '9G8F+5W'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_status'
            }),
            'first_contact_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'site_survey_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'contract_signed_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'project_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estimated_completion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'facility_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '5000'
            }),
            'facility_size_unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '100'
            }),
            'existing_systems': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List existing systems/equipment (JSON format or text)'
            }),
            'access_requirements': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_access_requirements'
            }),
            'work_hours': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_work_hours'
            }),
            'special_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Special safety, access, or work requirements'
            }),
            'emergency_contact_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Emergency contact information (JSON format)'
            }),
            'parking_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'loading_access': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'storage_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'custom_fields': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Custom data (JSON format)'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make business category and client required
        self.fields['business_category'].required = True
        self.fields['client'].required = True
        
        # Set up facility size unit choices
        self.fields['facility_size_unit'].choices = [
            ('sq_ft', 'Square Feet'),
            ('sq_m', 'Square Meters'),
            ('acres', 'Acres'),
            ('hectares', 'Hectares'),
            ('seats', 'Seats'),
            ('units', 'Units'),
        ]
        
        # Determine the selected business category
        category = None
        if self.instance and self.instance.business_category:
            category = self.instance.business_category
        elif self.data.get('business_category'):
            try:
                category = BusinessCategory.objects.get(pk=self.data.get('business_category'))
            except BusinessCategory.DoesNotExist:
                category = None

        # Filter location types based on business category
        if category:
            self.fields['location_type'].queryset = LocationType.objects.filter(
                business_category=category
            )
        else:
            self.fields['location_type'].queryset = LocationType.objects.none()

        # Set up dynamic choices for status, access requirements, and work hours
        if category:
            # Status choices
            status_choices = get_dynamic_choices('location_status', category)
            if status_choices:
                self.fields['status'].choices = status_choices

            # Access requirement choices
            access_choices = get_dynamic_choices('access_requirement', category)
            if access_choices:
                self.fields['access_requirements'].choices = access_choices

            # Work hours choices
            work_hours_choices = get_dynamic_choices('work_hours', category)
            if work_hours_choices:
                self.fields['work_hours'].choices = work_hours_choices
    
    def clean_latitude(self):
        """Validate latitude"""
        latitude = self.cleaned_data.get('latitude')
        if latitude is not None:
            if not -90 <= latitude <= 90:
                raise ValidationError('Latitude must be between -90 and 90 degrees.')
        return latitude
    
    def clean_longitude(self):
        """Validate longitude"""
        longitude = self.cleaned_data.get('longitude')
        if longitude is not None:
            if not -180 <= longitude <= 180:
                raise ValidationError('Longitude must be between -180 and 180 degrees.')
        return longitude
    
    def clean_google_plus_code(self):
        """Validate Google Plus Code format"""
        code = self.cleaned_data.get('google_plus_code', '').strip()
        if code:
            # Basic validation for Plus Code format (e.g., 9G8F+5W)
            if not (6 <= len(code) <= 15 and '+' in code):
                raise ValidationError('Invalid Google Plus Code format.')
        return code
    
    def clean_facility_size(self):
        """Validate facility size"""
        size = self.cleaned_data.get('facility_size')
        if size is not None and size <= 0:
            raise ValidationError('Facility size must be greater than zero.')
        return size
    
    def clean_capacity(self):
        """Validate capacity"""
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None and capacity <= 0:
            raise ValidationError('Capacity must be greater than zero.')
        return capacity


class LocationDocumentForm(ModelForm):
    """Form for uploading location documents"""
    
    class Meta:
        model = LocationDocument
        fields = [
            'document_type', 'title', 'description', 'file',
            'version', 'is_current', 'is_public'
        ]
        
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_document_type'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Document description'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control-file'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1.0'
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        location = kwargs.pop('location', None)
        super().__init__(*args, **kwargs)
        
        # Set up dynamic document type choices
        if location and location.business_category:
            doc_type_choices = get_dynamic_choices('document_type', location.business_category)
            if doc_type_choices:
                self.fields['document_type'].choices = doc_type_choices


class LocationNoteForm(ModelForm):
    """Form for creating location notes"""
    
    class Meta:
        model = LocationNote
        fields = [
            'note_type', 'title', 'content', 'priority',
            'is_client_visible', 'requires_followup', 'followup_date'
        ]
        
        widgets = {
            'note_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_note_type'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Note title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Note content'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_priority'
            }),
            'is_client_visible': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'requires_followup': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_requires_followup'
            }),
            'followup_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_followup_date'
            })
        }
    
    def __init__(self, *args, **kwargs):
        location = kwargs.pop('location', None)
        super().__init__(*args, **kwargs)
        
        # Set up dynamic choices
        if location and location.business_category:
            # Note type choices
            note_type_choices = get_dynamic_choices('note_type', location.business_category)
            if note_type_choices:
                self.fields['note_type'].choices = note_type_choices
            
            # Priority choices
            priority_choices = get_dynamic_choices('priority_level', location.business_category)
            if priority_choices:
                self.fields['priority'].choices = priority_choices
    
    def clean(self):
        """Validate followup requirements"""
        cleaned_data = super().clean()
        requires_followup = cleaned_data.get('requires_followup')
        followup_date = cleaned_data.get('followup_date')
        
        if requires_followup and not followup_date:
            raise ValidationError('Follow-up date is required when follow-up is needed.')
        
        return cleaned_data


# Address and Contact inline forms
class AddressForm(ModelForm):
    """Form for location addresses"""
    
    class Meta:
        model = Address
        fields = [
            'label', 'attention_line', 'line1', 'line2',
            'city', 'state_province', 'postal_code', 'country',
            'is_primary', 'is_active'
        ]
        
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'attention_line': forms.TextInput(attrs={'class': 'form-control'}),
            'line1': forms.TextInput(attrs={'class': 'form-control'}),
            'line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state_province': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ContactForm(ModelForm):
    """Form for location contacts"""
    
    class Meta:
        model = Contact
        fields = [
            'contact_type', 'first_name', 'last_name', 'title',
            'phone', 'mobile', 'email', 'department', 'notes',
            'is_primary', 'is_active'
        ]
        
        widgets = {
            'contact_type': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Formsets for inline editing

AddressFormSet = modelformset_factory(Address, fields='__all__')

ContactFormSet = modelformset_factory( Contact, fields='__all__')

# Search and filter forms
class LocationSearchForm(forms.Form):
    """Form for searching and filtering locations"""
    
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search locations, clients, or addresses...'
        })
    )
    
    business_category = forms.ModelChoiceField(
        queryset=BusinessCategory.objects.filter(is_active=True),
        required=False,
        empty_label='All Business Types',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + [
            ('prospect', 'Prospect'),
            ('active', 'Active'),
            ('complete', 'Complete'),
            ('inactive', 'Inactive')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    has_coordinates = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


# Quick create forms
class QuickLocationForm(forms.Form):
    """Simplified form for quick location creation"""
    
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Location name'
        })
    )
    
    client = forms.ModelChoiceField(
        queryset=Client.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    business_category = forms.ModelChoiceField(
        queryset=BusinessCategory.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Brief description'
        })
    )


class LocationImportForm(forms.Form):
    """Simple CSV import form for locations."""

    csv_file = forms.FileField(
        label="CSV File",
        help_text="Upload CSV file with location data",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )

    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']

        if file:
            name = file.name.lower()
            if not name.endswith('.csv'):
                raise ValidationError('File must be CSV format.')

            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size cannot exceed 10MB.')

        return file
