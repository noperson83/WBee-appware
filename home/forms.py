# home/forms.py
"""
Clean Django forms for the home app.
Simple, focused forms without unnecessary complexity.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import UserPreference, Announcement

User = get_user_model()


class ContactForm(forms.Form):
    """Simple contact form with basic validation."""
    
    from_email = forms.EmailField(
        label='Your Email',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    
    subject = forms.CharField(
        label='Subject',
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'What is this regarding?'
        })
    )
    
    message = forms.CharField(
        label='Message',
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Please provide details about your inquiry...'
        })
    )
    
    def clean_message(self):
        """Validate message content."""
        message = self.cleaned_data['message']
        
        if len(message) < 10:
            raise ValidationError('Message must be at least 10 characters long.')
        
        # Basic spam filtering
        spam_keywords = ['viagra', 'casino', 'lottery', 'winner']
        if any(keyword in message.lower() for keyword in spam_keywords):
            raise ValidationError('Message contains inappropriate content.')
        
        return message


class UserPreferenceForm(forms.ModelForm):
    """Form for user preferences and settings."""
    
    class Meta:
        model = UserPreference
        fields = [
            'theme', 'sidebar_collapsed', 'items_per_page',
            'email_notifications', 'browser_notifications',
            'date_format', 'timezone'
        ]
        
        widgets = {
            'items_per_page': forms.NumberInput(attrs={
                'min': 10, 'max': 100, 'class': 'form-control'
            }),
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'date_format': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('%Y-%m-%d', '2024-01-15 (YYYY-MM-DD)'),
                ('%m/%d/%Y', '01/15/2024 (MM/DD/YYYY)'),
                ('%d/%m/%Y', '15/01/2024 (DD/MM/YYYY)'),
                ('%B %d, %Y', 'January 15, 2024'),
            ]),
            'timezone': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('America/Phoenix', 'Arizona (MST)'),
                ('America/New_York', 'Eastern Time'),
                ('America/Chicago', 'Central Time'),
                ('America/Denver', 'Mountain Time'),
                ('America/Los_Angeles', 'Pacific Time'),
                ('UTC', 'UTC'),
            ]),
            'sidebar_collapsed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'browser_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AnnouncementForm(forms.ModelForm):
    """Form for creating company announcements."""
    
    class Meta:
        model = Announcement
        fields = [
            'title', 'content', 'announcement_type', 'priority',
            'publish_date', 'expiry_date', 'show_on_dashboard',
            'require_acknowledgment'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 6, 'class': 'form-control'}),
            'announcement_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'publish_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'expiry_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'show_on_dashboard': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_acknowledgment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class QuickSearchForm(forms.Form):
    """Quick search form for dashboard search functionality."""
    
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search...',
            'autocomplete': 'off',
        })
    )
    
    search_type = forms.ChoiceField(
        choices=[
            ('all', 'All'),
            ('assets', 'Assets'),
            ('projects', 'Projects'),
            ('announcements', 'Announcements'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )