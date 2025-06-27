# client/forms.py - Complete Forms Implementation

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Client, Address, Contact
import datetime

class ClientForm(forms.ModelForm):
    """Comprehensive client form with validation"""
    
    # Contact fields (for primary contact creation)
    contact_first_name = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        }),
        label='First Name'
    )
    contact_last_name = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        }),
        label='Last Name'
    )
    contact_title = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., CEO, Manager, Owner'
        }),
        label='Job Title'
    )
    contact_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'contact@company.com'
        }),
        label='Email Address'
    )
    contact_phone = forms.CharField(
        max_length=17, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(555) 123-4567'
        }),
        label='Phone Number'
    )
    contact_type = forms.ChoiceField(
        choices=Contact.CONTACT_TYPES,
        initial='primary',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Contact Type'
    )
    
    # Address fields (for primary address creation)
    billing_attention = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Attn: John Doe (optional)'
        }),
        label='Attention Line'
    )
    billing_address = forms.CharField(
        max_length=200, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123 Main Street'
        }),
        label='Street Address'
    )
    billing_address2 = forms.CharField(
        max_length=200, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Suite 100 (optional)'
        }),
        label='Address Line 2'
    )
    billing_city = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        }),
        label='City'
    )
    billing_state = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'State or Province'
        }),
        label='State/Province'
    )
    billing_zipcode = forms.CharField(
        max_length=20, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345'
        }),
        label='ZIP/Postal Code'
    )
    billing_country = forms.CharField(
        max_length=2,
        initial='US',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'value': 'US'
        }),
        label='Country Code'
    )

    class Meta:
        model = Client
        fields = [
            'company_name', 'company_url', 'logo', 'business_type', 'tax_id',
            'status', 'date_of_contact', 'date_of_contract', 'payment_terms',
            'credit_limit', 'summary'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name'
            }),
            'company_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'business_type': forms.Select(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XX-XXXXXXX',
                'maxlength': '20'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'date_of_contact': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_of_contract': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_terms': forms.Select(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Brief description of the client, their needs, and your relationship...',
                'maxlength': '2000'
            })
        }

    def clean_company_name(self):
        """Validate company name"""
        company_name = self.cleaned_data.get('company_name')
        if not company_name or not company_name.strip():
            raise ValidationError(_('Company name is required.'))
        return company_name.strip()

    def clean_company_url(self):
        """Validate company URL"""
        url = self.cleaned_data.get('company_url')
        if url and not url.startswith(('http://', 'https://')):
            raise ValidationError(_('URL must start with http:// or https://'))
        return url

    def clean_date_of_contact(self):
        """Validate contact date"""
        data = self.cleaned_data.get('date_of_contact')
        if data:
            # Check date is not too far in the future
            if data > datetime.date.today() + datetime.timedelta(weeks=4):
                raise ValidationError(_('Contact date cannot be more than 4 weeks in the future.'))
        return data

    def clean_date_of_contract(self):
        """Validate contract date"""
        data = self.cleaned_data.get('date_of_contract')
        contact_date = self.cleaned_data.get('date_of_contact')
        
        if data and contact_date:
            if data < contact_date:
                raise ValidationError(_('Contract date cannot be before contact date.'))
        return data

    def clean_credit_limit(self):
        """Validate credit limit"""
        credit_limit = self.cleaned_data.get('credit_limit')
        if credit_limit and credit_limit < 0:
            raise ValidationError(_('Credit limit cannot be negative.'))
        return credit_limit

    def clean_contact_email(self):
        """Validate contact email"""
        email = self.cleaned_data.get('contact_email')
        if email:
            # Check if another client already has this email as primary contact
            existing_contact = Contact.objects.filter(
                email=email,
                is_primary=True,
                content_type__model='client'
            ).exclude(
                object_id=self.instance.pk if self.instance else None
            ).first()
            
            if existing_contact:
                raise ValidationError(
                    _('This email is already used as a primary contact for another client.')
                )
        return email

    def save(self, commit=True):
        """Override save to handle related objects"""
        client = super().save(commit=commit)
        
        if commit:
            # Create or update primary contact
            self._save_primary_contact(client)
            
            # Create or update primary address
            self._save_primary_address(client)
        
        return client

    def _save_primary_contact(self, client):
        """Create or update primary contact"""
        contact_data = {
            'first_name': self.cleaned_data.get('contact_first_name', ''),
            'last_name': self.cleaned_data.get('contact_last_name', ''),
            'title': self.cleaned_data.get('contact_title', ''),
            'email': self.cleaned_data.get('contact_email', ''),
            'phone': self.cleaned_data.get('contact_phone', ''),
            'contact_type': self.cleaned_data.get('contact_type', 'primary'),
        }
        
        # Only create/update if we have meaningful contact data
        if any([contact_data['first_name'], contact_data['last_name'], 
                contact_data['email'], contact_data['phone']]):
            
            # Get or create primary contact
            contact, created = Contact.objects.get_or_create(
                content_object=client,
                is_primary=True,
                defaults=contact_data
            )
            
            if not created:
                # Update existing contact
                for field, value in contact_data.items():
                    setattr(contact, field, value)
                contact.save()

    def _save_primary_address(self, client):
        """Create or update primary address"""
        address_data = {
            'attention_line': self.cleaned_data.get('billing_attention', ''),
            'line1': self.cleaned_data.get('billing_address', ''),
            'line2': self.cleaned_data.get('billing_address2', ''),
            'city': self.cleaned_data.get('billing_city', ''),
            'state_province': self.cleaned_data.get('billing_state', ''),
            'postal_code': self.cleaned_data.get('billing_zipcode', ''),
            'country': self.cleaned_data.get('billing_country', 'US'),
            'label': 'billing',
        }
        
        # Only create/update if we have a street address
        if address_data['line1']:
            # Get or create primary address
            address, created = Address.objects.get_or_create(
                content_object=client,
                is_primary=True,
                defaults=address_data
            )
            
            if not created:
                # Update existing address
                for field, value in address_data.items():
                    setattr(address, field, value)
                address.save()


class AddressForm(forms.ModelForm):
    """Form for adding/editing addresses"""
    
    class Meta:
        model = Address
        fields = [
            'label', 'attention_line', 'line1', 'line2', 
            'city', 'state_province', 'postal_code', 'country',
            'is_primary', 'is_active'
        ]
        widgets = {
            'label': forms.Select(attrs={'class': 'form-control'}),
            'attention_line': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Attn: John Doe'
            }),
            'line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street address'
            }),
            'line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apt, Suite, etc.'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state_province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State or Province'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ZIP or Postal Code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'US'
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ContactForm(forms.ModelForm):
    """Form for adding/editing contacts"""
    
    class Meta:
        model = Contact
        fields = [
            'contact_type', 'first_name', 'last_name', 'title',
            'phone', 'mobile', 'email', 'department', 'notes',
            'is_primary', 'is_active'
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
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 987-6543'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Department'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_email(self):
        """Validate email uniqueness for primary contacts"""
        email = self.cleaned_data.get('email')
        is_primary = self.cleaned_data.get('is_primary', False)
        
        if email and is_primary:
            # Check if another client already has this email as primary contact
            existing = Contact.objects.filter(
                email=email,
                is_primary=True,
                content_type__model='client'
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise ValidationError(
                    _('This email is already used as a primary contact for another client.')
                )
        
        return email
