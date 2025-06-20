# asset/forms.py - Clean modern forms for asset management
"""
Modern Django forms for asset management.
Clean, focused forms without legacy compatibility.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML
from crispy_forms.bootstrap import FormActions

from .models import (
    Asset,
    AssetCategory,
    AssetMaintenanceRecord,
    AssetAssignment,
    Condition,
)
from hr.models import Worker
from project.models import Project
from company.models import Office, Department

User = get_user_model()


class AssetForm(forms.ModelForm):
    """Main form for creating and editing assets."""
    
    class Meta:
        model = Asset
        fields = [
            'asset_number', 'name', 'category', 'asset_type',
            'manufacturer', 'model', 'year', 'serial_number',
            'description', 'primary_image',
            'purchase_price', 'current_value', 'purchase_date', 'warranty_expiration',
            'assigned_office', 'assigned_department', 'assigned_worker', 'current_project',
            'status', 'location_status', 'condition',
            'usage_hours', 'mileage', 'is_personal', 'is_billable', 'hourly_rate',
        ]
        
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warranty_expiration': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'purchase_price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'current_value': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'usage_hours': forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter choices based on user's company
        if self.user and hasattr(self.user, 'company'):
            company = self.user.company
            
            self.fields['assigned_office'].queryset = Office.objects.filter(company=company)
            self.fields['assigned_department'].queryset = Department.objects.filter(company=company)
            self.fields['assigned_worker'].queryset = Worker.objects.filter(
                company=company, is_active=True
            )
            self.fields['current_project'].queryset = Project.objects.filter(
                client__company=company, status__in=['planning', 'active']
            )
    
    def clean_asset_number(self):
        """Validate asset number is unique."""
        asset_number = self.cleaned_data['asset_number']
        
        if asset_number:
            # Check for duplicates, excluding current instance if editing
            queryset = Asset.objects.filter(asset_number=asset_number)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError('Asset number must be unique.')
        
        return asset_number
    
    def clean(self):
        """Additional form validation."""
        cleaned_data = super().clean()
        
        # Validate purchase vs current value
        purchase_price = cleaned_data.get('purchase_price')
        current_value = cleaned_data.get('current_value')
        
        if purchase_price and current_value and current_value > purchase_price:
            raise ValidationError(
                'Current value cannot be greater than purchase price.'
            )
        
        # Validate warranty expiration
        purchase_date = cleaned_data.get('purchase_date')
        warranty_expiration = cleaned_data.get('warranty_expiration')
        
        if purchase_date and warranty_expiration and warranty_expiration < purchase_date:
            raise ValidationError(
                'Warranty expiration cannot be before purchase date.'
            )
        
        return cleaned_data


class AssetSearchForm(forms.Form):
    """Form for searching and filtering assets."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search assets...',
            'class': 'form-control'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=AssetCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + [
            ('available', 'Available'),
            ('in_use', 'In Use'),
            ('maintenance', 'Under Maintenance'),
            ('repair', 'Being Repaired'),
            ('retired', 'Retired'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=Worker.objects.filter(is_active=True),
        required=False,
        empty_label="All Workers",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter by user's company
        if self.user and hasattr(self.user, 'company'):
            self.fields['assigned_to'].queryset = Worker.objects.filter(
                company=self.user.company, is_active=True
            )


class AssetAssignmentForm(forms.ModelForm):
    """Form for assigning assets to workers or projects."""
    
    class Meta:
        model = AssetAssignment
        fields = [
            'assigned_to_worker', 'assigned_to_project', 'assigned_to_office',
            'start_date', 'end_date', 'purpose', 'notes'
        ]
        
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set default start date to today
        self.fields['start_date'].initial = timezone.now().date()
        
        # Filter choices by user's company
        if self.user and hasattr(self.user, 'company'):
            company = self.user.company
            
            self.fields['assigned_to_worker'].queryset = Worker.objects.filter(
                company=company, is_active=True
            )
            self.fields['assigned_to_project'].queryset = Project.objects.filter(
                client__company=company, status__in=['planning', 'active']
            )
            self.fields['assigned_to_office'].queryset = Office.objects.filter(
                company=company
            )
    
    def clean(self):
        """Validate assignment dates."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date <= start_date:
            raise ValidationError('End date must be after start date.')
        
        # Must assign to at least one entity
        assigned_to_worker = cleaned_data.get('assigned_to_worker')
        assigned_to_project = cleaned_data.get('assigned_to_project')
        assigned_to_office = cleaned_data.get('assigned_to_office')
        
        if not any([assigned_to_worker, assigned_to_project, assigned_to_office]):
            raise ValidationError(
                'Asset must be assigned to at least a worker, project, or office.'
            )
        
        return cleaned_data


class AssetMaintenanceForm(forms.ModelForm):
    """Form for recording asset maintenance."""
    
    class Meta:
        model = AssetMaintenanceRecord
        fields = [
            'maintenance_type', 'description', 'performed_by', 'performed_date',
            'labor_cost', 'parts_cost', 'external_cost', 'parts_used',
            'issue_resolved', 'follow_up_required', 'follow_up_date'
        ]
        
        widgets = {
            'performed_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'labor_cost': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'parts_cost': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'external_cost': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'parts_used': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'performed_by': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default values
        self.fields['performed_date'].initial = timezone.now().date()
        self.fields['issue_resolved'].initial = True


class AssetBulkUpdateForm(forms.Form):
    """Form for bulk updating multiple assets."""
    
    status = forms.ChoiceField(
        choices=[('', 'No Change')] + [
            ('available', 'Available'),
            ('in_use', 'In Use'),
            ('maintenance', 'Under Maintenance'),
            ('repair', 'Being Repaired'),
            ('retired', 'Retired'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned_office = forms.ModelChoiceField(
        queryset=Office.objects.all(),
        required=False,
        empty_label="No Change",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned_department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="No Change",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    condition = forms.ChoiceField(
        choices=[('', 'No Change')] + list(Condition.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter by user's company
        if self.user and hasattr(self.user, 'company'):
            company = self.user.company
            self.fields['assigned_office'].queryset = Office.objects.filter(company=company)
            self.fields['assigned_department'].queryset = Department.objects.filter(company=company)


class AssetImportForm(forms.Form):
    """Form for importing assets from CSV."""
    
    csv_file = forms.FileField(
        label="CSV File",
        help_text="Upload CSV file with asset data",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )
    
    update_existing = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Update existing assets if asset number matches",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_csv_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data['csv_file']
        
        if file:
            # Check file extension
            name = file.name.lower()
            if not name.endswith('.csv'):
                raise ValidationError('File must be CSV format.')
            
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size cannot exceed 10MB.')
        
        return file


class AssetCategoryForm(forms.ModelForm):
    """Form for creating and editing asset categories."""
    
    class Meta:
        model = AssetCategory
        fields = [
            'name', 'description', 'business_category', 'icon', 'color',
            'is_active'
        ]
        
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-icon-name'}),
        }


class AssetBulkAssignForm(forms.Form):
    """Form for bulk assigning multiple assets."""
    
    assigned_to_worker = forms.ModelChoiceField(
        queryset=Worker.objects.filter(is_active=True),
        required=False,
        empty_label="Select Worker",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned_to_project = forms.ModelChoiceField(
        queryset=Project.objects.filter(status__in=['planning', 'active']),
        required=False,
        empty_label="Select Project", 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assigned_to_office = forms.ModelChoiceField(
        queryset=Office.objects.all(),
        required=False,
        empty_label="Select Office",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    purpose = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Purpose of assignment'
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Additional notes'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter by user's company
        if self.user and hasattr(self.user, 'company'):
            company = self.user.company
            
            self.fields['assigned_to_worker'].queryset = Worker.objects.filter(
                company=company, is_active=True
            )
            self.fields['assigned_to_project'].queryset = Project.objects.filter(
                client__company=company, status__in=['planning', 'active']
            )
            self.fields['assigned_to_office'].queryset = Office.objects.filter(
                company=company
            )
    
    def clean(self):
        """Validate that at least one assignment target is selected."""
        cleaned_data = super().clean()
        
        assigned_to_worker = cleaned_data.get('assigned_to_worker')
        assigned_to_project = cleaned_data.get('assigned_to_project')
        assigned_to_office = cleaned_data.get('assigned_to_office')
        
        if not any([assigned_to_worker, assigned_to_project, assigned_to_office]):
            raise ValidationError(
                'Must assign to at least a worker, project, or office.'
            )
        
        return cleaned_data


class AssetFilterForm(forms.Form):
    """Advanced filtering form for assets."""
    
    purchase_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    purchase_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    value_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    value_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    condition = forms.ChoiceField(
        choices=[('', 'All Conditions')] + list(Condition.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    maintenance_due = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


# Quick forms for common actions
class QuickAssignForm(forms.Form):
    """Quick assignment form for mobile/AJAX use."""
    
    worker = forms.ModelChoiceField(
        queryset=Worker.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and hasattr(self.user, 'company'):
            self.fields['worker'].queryset = Worker.objects.filter(
                company=self.user.company, is_active=True
            )


class QuickStatusForm(forms.Form):
    """Quick status update form for mobile/AJAX use."""
    
    status = forms.ChoiceField(
        choices=[
            ('available', 'Available'),
            ('in_use', 'In Use'),
            ('maintenance', 'Under Maintenance'),
            ('repair', 'Being Repaired'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
