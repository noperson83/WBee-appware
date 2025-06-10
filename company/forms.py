# company/forms.py - Modern Forms for Company Management

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

from .models import Company, Office, Department, CompanySettings
from client.models import Address, Contact
from location.models import BusinessCategory


class CompanyForm(forms.ModelForm):
    """Enhanced form for creating and updating companies"""
    
    class Meta:
        model = Company
        fields = [
            'company_name', 'legal_name', 'company_url', 'logo', 'button_image',
            'brand_colors', 'business_category', 'business_type', 'tax_id', 
            'business_license', 'primary_contact_name', 'primary_contact_title', 
            'primary_phone', 'primary_email', 'description', 'mission_statement', 
            'founded_date', 'current_year_revenue', 'previous_year_revenue',
            'timezone', 'currency', 'fiscal_year_start', 'default_payment_terms',
            'is_multi_location', 'parent_company', 'custom_fields'
        ]
        
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name'
            }),
            'legal_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Legal business name (if different)'
            }),
            'company_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://company.com'
            }),
            'business_category': forms.Select(attrs={'class': 'form-control'}),
            'business_type': forms.Select(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'EIN or Tax ID'
            }),
            'business_license': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business license number'
            }),
            'primary_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primary contact name'
            }),
            'primary_contact_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Title/Position'
            }),
            'primary_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'primary_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@company.com'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Brief description of the company'
            }),
            'mission_statement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Company mission statement'
            }),
            'founded_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'current_year_revenue': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'previous_year_revenue': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'timezone': forms.Select(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'fiscal_year_start': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 12
            }),
            'default_payment_terms': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Net 30'
            }),
            'parent_company': forms.Select(attrs={'class': 'form-control'}),
            'custom_fields': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Custom JSON data (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields required
        self.fields['company_name'].required = True
        self.fields['primary_contact_name'].required = True
        
        # Filter parent company choices (exclude self)
        if self.instance.pk:
            self.fields['parent_company'].queryset = Company.objects.filter(
                is_active=True
            ).exclude(pk=self.instance.pk)
        else:
            self.fields['parent_company'].queryset = Company.objects.filter(is_active=True)
        
        # Add help text
        self.fields['fiscal_year_start'].help_text = 'Month number (1=January, 4=April, etc.)'
        self.fields['brand_colors'].help_text = 'JSON format: {"primary": "#color", "secondary": "#color"}'
        self.fields['custom_fields'].help_text = 'JSON format for additional company data'
    
    def clean_founded_date(self):
        """Validate founded date is not in the future"""
        founded_date = self.cleaned_data.get('founded_date')
        if founded_date and founded_date > date.today():
            raise ValidationError("Founded date cannot be in the future.")
        return founded_date
    
    def clean_fiscal_year_start(self):
        """Validate fiscal year start month"""
        month = self.cleaned_data.get('fiscal_year_start')
        if month and (month < 1 or month > 12):
            raise ValidationError("Fiscal year start must be between 1 and 12.")
        return month
    
    def clean(self):
        """Additional form validation"""
        cleaned_data = super().clean()
        parent_company = cleaned_data.get('parent_company')
        is_multi_location = cleaned_data.get('is_multi_location')
        
        # If parent company is set, this should be a subsidiary
        if parent_company and parent_company == self.instance:
            raise ValidationError("A company cannot be its own parent.")
        
        return cleaned_data


class OfficeForm(forms.ModelForm):
    """Form for creating and updating offices"""
    
    class Meta:
        model = Office
        fields = [
            'company', 'office_name', 'office_code', 'office_type', 'description',
            'employee_capacity', 'square_footage', 'office_manager', 'phone_number',
            'email', 'operating_hours', 'opened_date', 'is_active'
        ]
        
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'office_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Office name (e.g., Headquarters, Phoenix Branch)'
            }),
            'office_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Short code (e.g., HQ, PHX)'
            }),
            'office_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Office description and details'
            }),
            'employee_capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Maximum number of employees'
            }),
            'square_footage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Size in square feet'
            }),
            'office_manager': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Office manager name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'office@company.com'
            }),
            'operating_hours': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'JSON format: {"monday": "9:00-17:00", ...}'
            }),
            'opened_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        
        # If company_id is provided, filter the company field
        if company_id:
            self.fields['company'].queryset = Company.objects.filter(id=company_id)
            self.fields['company'].initial = company_id
        else:
            self.fields['company'].queryset = Company.objects.filter(is_active=True)
    
    def clean_opened_date(self):
        """Validate opened date"""
        opened_date = self.cleaned_data.get('opened_date')
        if opened_date and opened_date > date.today():
            raise ValidationError("Opened date cannot be in the future.")
        return opened_date


class DepartmentForm(forms.ModelForm):
    """Form for creating and updating departments"""
    
    class Meta:
        model = Department
        fields = [
            'company', 'name', 'department_code', 'description', 'parent_department',
            'department_head', 'annual_budget', 'cost_center_code', 'primary_office',
            'is_billable', 'is_active'
        ]
        
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department name (e.g., Sales, IT, Human Resources)'
            }),
            'department_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Short code (e.g., SALES, IT, HR)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Department description and responsibilities'
            }),
            'parent_department': forms.Select(attrs={'class': 'form-control'}),
            'department_head': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department head/manager name'
            }),
            'annual_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'cost_center_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cost center code for accounting'
            }),
            'primary_office': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        
        # Filter querysets based on company
        if company_id:
            company = Company.objects.get(id=company_id)
            self.fields['company'].queryset = Company.objects.filter(id=company_id)
            self.fields['company'].initial = company_id
            self.fields['parent_department'].queryset = Department.objects.filter(
                company=company, is_active=True
            )
            self.fields['primary_office'].queryset = Office.objects.filter(
                company=company, is_active=True
            )
        else:
            self.fields['company'].queryset = Company.objects.filter(is_active=True)
        
        # Exclude self from parent department choices
        if self.instance.pk:
            self.fields['parent_department'].queryset = self.fields['parent_department'].queryset.exclude(
                pk=self.instance.pk
            )
    
    def clean(self):
        """Additional validation for departments"""
        cleaned_data = super().clean()
        parent_department = cleaned_data.get('parent_department')
        company = cleaned_data.get('company')
        
        # Ensure parent department belongs to same company
        if parent_department and parent_department.company != company:
            raise ValidationError("Parent department must belong to the same company.")
        
        # Prevent circular references
        if parent_department and parent_department == self.instance:
            raise ValidationError("A department cannot be its own parent.")
        
        return cleaned_data


class CompanySettingsForm(forms.ModelForm):
    """Form for company settings"""
    
    class Meta:
        model = CompanySettings
        fields = [
            'invoice_prefix', 'next_invoice_number', 'project_prefix', 
            'next_project_number', 'smtp_server', 'smtp_port', 'smtp_username',
            'smtp_use_tls', 'date_format', 'notification_settings', 'integrations'
        ]
        
        widgets = {
            'invoice_prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'INV'
            }),
            'next_invoice_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'project_prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'P'
            }),
            'next_project_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'smtp_server': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'smtp.gmail.com'
            }),
            'smtp_port': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '587'
            }),
            'smtp_username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@company.com'
            }),
            'date_format': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'MM/DD/YYYY'
            }),
            'notification_settings': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'JSON format notification preferences'
            }),
            'integrations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'JSON format integration settings'
            }),
        }


class AddressForm(forms.ModelForm):
    """Form for company addresses"""
    
    class Meta:
        model = Address
        fields = [
            'label', 'attention_line', 'line1', 'line2', 'city', 
            'state_province', 'postal_code', 'country', 'is_primary'
        ]
        
        widgets = {
            'label': forms.Select(attrs={'class': 'form-control'}),
            'attention_line': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Attention line (optional)'
            }),
            'line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street address'
            }),
            'line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apt, suite, etc. (optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state_province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State/Province'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ZIP/Postal Code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),
        }


class ContactForm(forms.ModelForm):
    """Form for company contacts"""
    
    class Meta:
        model = Contact
        fields = [
            'contact_type', 'first_name', 'last_name', 'title', 'department',
            'phone', 'mobile', 'email', 'notes', 'is_primary'
        ]
        
        widgets = {
            'contact_type': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job title'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@company.com'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about this contact'
            }),
        }


class CompanySearchForm(forms.Form):
    """Form for searching companies"""
    
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search companies...',
            'id': 'company-search'
        })
    )
    
    business_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Company.BUSINESS_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    business_category = forms.ModelChoiceField(
        queryset=BusinessCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    active_status = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('true', 'Active Only'),
            ('false', 'Inactive Only')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# Formsets for inline editing
from django.forms import inlineformset_factory

# Address formset for companies
CompanyAddressFormSet = inlineformset_factory(
    Company,
    Address,
    form=AddressForm,
    extra=1,
    can_delete=True,
    fields=['label', 'line1', 'line2', 'city', 'state_province', 'postal_code', 'is_primary']
)

# Contact formset for companies  
CompanyContactFormSet = inlineformset_factory(
    Company,
    Contact,
    form=ContactForm,
    extra=1,
    can_delete=True,
    fields=['contact_type', 'first_name', 'last_name', 'title', 'phone', 'email', 'is_primary']
)

# Office formset for companies
CompanyOfficeFormSet = inlineformset_factory(
    Company,
    Office,
    form=OfficeForm,
    extra=0,
    can_delete=True,
    fields=['office_name', 'office_type', 'office_manager', 'phone_number', 'is_active']
)

# Department formset for companies
CompanyDepartmentFormSet = inlineformset_factory(
    Company,
    Department,
    form=DepartmentForm,
    extra=0,
    can_delete=True,
    fields=['name', 'department_code', 'department_head', 'is_billable', 'is_active']
)