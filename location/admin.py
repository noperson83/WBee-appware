# location/admin.py - Modern Admin Interface for Locations

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.utils import timezone
from django.conf import settings
from decimal import Decimal, ROUND_DOWN

from .models import (
    BusinessCategory, ConfigurableChoice, LocationType, Location, 
    LocationDocument, LocationNote
)
from client.models import Address, Contact

# Inline admins for related models
class AddressInline(GenericTabularInline):
    """Inline admin for addresses"""
    model = Address
    extra = 1
    fields = (
        'label', 'attention_line', 'line1', 'line2', 
        'city', 'state_province', 'postal_code', 
        'is_primary', 'is_active'
    )
    readonly_fields = ('created_at', 'updated_at')

class ContactInline(GenericTabularInline):
    """Inline admin for contacts"""
    model = Contact
    extra = 1
    fields = (
        'contact_type', 'first_name', 'last_name', 'title',
        'phone', 'email', 'is_primary', 'is_active'
    )
    readonly_fields = ('created_at', 'updated_at')

class LocationDocumentInline(admin.TabularInline):
    """Inline admin for location documents"""
    model = LocationDocument
    extra = 0
    fields = (
        'document_type', 'title', 'file', 'version', 
        'is_current', 'is_public'
    )
    readonly_fields = ('created_at', 'updated_at')

class LocationNoteInline(admin.TabularInline):
    """Inline admin for location notes"""
    model = LocationNote
    extra = 0
    fields = (
        'note_type', 'title', 'priority', 'requires_followup', 
        'followup_date', 'is_client_visible'
    )
    readonly_fields = ('created_at', 'updated_at')

# Business Category Admin
@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'project_terminology',
        'client_nickname',
        'icon_display',
        'color_display',
        'location_count',
        'is_active'
    )
    
    list_filter = (
        'is_active',
        'created_at'
    )
    
    search_fields = ('name', 'description')
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'description',
                'is_active'
            )
        }),
        ('Project Terminology', {
            'fields': (
                'project_nickname',
                'project_nickname_singular'
            ),
            'description': 'Customize what "Projects" are called in this business type'
        }),
        ('Client Terminology', {
            'fields': (
                'client_nickname',
                'client_nickname_singular',
                'client_nickname_options'
            ),
            'description': 'Alternate names for clients',
            'classes': ('collapse',)
        }),
        ('Visual Settings', {
            'fields': (
                'icon',
                'color'
            ),
            'classes': ('collapse',)
        })
    )
    
    def project_terminology(self, obj):
        return f"{obj.project_nickname} ({obj.project_nickname_singular})"
    project_terminology.short_description = 'Project Terms'
    
    def icon_display(self, obj):
        if obj.icon:
            return format_html('<i class="{}" style="color: {};"></i> {}', obj.icon, obj.color, obj.icon)
        return "—"
    icon_display.short_description = 'Icon'
    
    def color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; display: inline-block; margin-right: 5px;"></div>{}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    def location_count(self, obj):
        count = obj.location_types.count()
        return f"{count} location types"
    location_count.short_description = 'Location Types'

# Configurable Choice Admin
@admin.register(ConfigurableChoice)
class ConfigurableChoiceAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'choice_type',
        'category',
        'value',
        'sort_order',
        'is_active',
        'applicable_to_all'
    )
    
    list_filter = (
        'choice_type',
        'category',
        'is_active',
        'applicable_to_all'
    )
    
    search_fields = (
        'display_name',
        'value',
        'description'
    )
    
    list_editable = (
        'sort_order',
        'is_active'
    )
    
    fieldsets = (
        ('Choice Information', {
            'fields': (
                'category',
                'choice_type',
                'value',
                'display_name',
                'description'
            )
        }),
        ('Settings', {
            'fields': (
                'sort_order',
                'is_active',
                'is_default',
                'applicable_to_all'
            )
        })
    )

# Location Type Admin
@admin.register(LocationType)
class LocationTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'business_category',
        'location_count',
        'created_at'
    )
    
    list_filter = (
        'business_category',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description'
    )
    
    def location_count(self, obj):
        # Fixed: Need to use proper reverse relationship
        try:
            count = Location.objects.filter(location_type=obj).count()
            return f"{count} locations"
        except:
            return "0 locations"
    location_count.short_description = 'Locations Using This Type'

# Main Location Admin
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'client',
        'business_category_display',
        'status_badge',
        'location_type',
        'coordinates_display',
        'project_count',
        'total_value_display',
        'contract_signed_date'
    )

    list_filter = (
        'status',
        'business_category',
        'location_type',
        'contract_signed_date',
        'created_at',
        'parking_available',
        'loading_access'
    )

    search_fields = (
        'name',
        'description',
        'client__company_name',
        'contacts__first_name',
        'contacts__last_name',
        'contacts__email',
        'addresses__city',
        'addresses__state_province'
    )

    readonly_fields = (
        'id',
        'total_contract_value',
        'created_at',
        'updated_at',
        'profile_image_preview',
        'coordinates_map',
        'quick_stats',
        'project_term_display'
    )

    date_hierarchy = 'contract_signed_date'

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'client',
                'business_category',
                'location_type',
                'status'
            )
        }),
        ('Description', {
            'fields': (
                'description',
                'scope_summary',
                ('profile_image', 'profile_image_preview')
            )
        }),
        ('Location Details', {
            'fields': (
                'location_category',
                ('latitude', 'longitude'),
                'coordinates_map',
                'google_maps_url',
                'google_plus_code'
            )
        }),
        ('Dates & Timeline', {
            'fields': (
                'first_contact_date',
                'site_survey_date',
                'contract_signed_date',
                'project_start_date',
                'estimated_completion'
            )
        }),
        ('Facility Information', {
            'fields': (
                ('facility_size', 'facility_size_unit'),
                'capacity',
                'existing_systems'
            ),
            'classes': ('collapse',)
        }),
        ('Access & Logistics', {
            'fields': (
                'access_requirements',
                'work_hours',
                'special_requirements',
                'delivery_restrictions',
                'storage_limitations',
                'environmental_conditions',
                ('parking_available', 'loading_access', 'storage_available')
            ),
            'classes': ('collapse',)
        }),
        ('Financial Summary', {
            'fields': (
                'total_contract_value',
                'quick_stats'
            ),
            'classes': ('collapse',)
        }),
        ('Emergency & Contact Info', {
            'fields': (
                'emergency_contact_info',
            ),
            'classes': ('collapse',)
        }),
        ('Custom Data', {
            'fields': (
                'custom_fields',
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': (
                'id',
                'project_term_display',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [AddressInline, ContactInline, LocationDocumentInline, LocationNoteInline]

    actions = ['calculate_contract_values', 'mark_as_active', 'mark_as_inactive']

    # Custom display methods
    def business_category_display(self, obj):
        if obj.business_category:
            return format_html(
                '<span style="color: {}; font-weight: bold;"><i class="{}"></i> {}</span>',
                obj.business_category.color,
                obj.business_category.icon,
                obj.business_category.name
            )
        return "—"
    business_category_display.short_description = 'Business Type'

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'prospect': '#FFA500',
            'active': '#28A745',
            'complete': '#6C757D',
            'inactive': '#DC3545'
        }
        # Default color for custom statuses
        color = colors.get(obj.status, '#007BFF')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status.replace('_', ' ').title()
        )
    status_badge.short_description = 'Status'

    def coordinates_display(self, obj):
        """Display GPS coordinates"""
        if obj.coordinates:
            lat, lng = obj.coordinates
            # Ensure values are plain floats to avoid SafeString formatting errors
            lat = float(lat)
            lng = float(lng)
            return format_html(
                '<a href="https://www.google.com/maps?q={},{}" target="_blank">{}, {}</a>',
                lat,
                lng,
                f"{lat:.4f}",
                f"{lng:.4f}"
            )
        return "—"
    coordinates_display.short_description = 'GPS Coordinates'

    def project_count(self, obj):
        """Display number of projects with business-specific terminology"""
        try:
            from project.models import Project
            count = Project.objects.filter(location=obj).count()
            term = obj.project_term.lower() if count != 1 else obj.project_term_singular.lower()
            
            if count > 0:
                url = reverse('admin:project_project_changelist') + f'?location__id__exact={obj.id}'
                return format_html('<a href="{}">{} {}</a>', url, count, term)
            return f"0 {term}"
        except:
            return "—"
    project_count.short_description = 'Projects'

    def total_value_display(self, obj):
        """Display total contract value with formatting"""
        if obj.total_contract_value:
            return f"${obj.total_contract_value:,.2f}"
        return "—"
    total_value_display.short_description = 'Total Value'

    def profile_image_preview(self, obj):
        """Display profile image preview"""
        if obj.profile_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.profile_image.url
            )
        return "No image"
    profile_image_preview.short_description = 'Image Preview'

    def coordinates_map(self, obj):
        """Display embedded map if coordinates available"""
        if obj.coordinates:
            lat, lng = obj.coordinates
            return format_html(
                '<iframe width="300" height="200" src="https://www.google.com/maps/embed/v1/place?key={key}&q={lat},{lng}" allowfullscreen></iframe>',
                key=settings.GOOGLE_MAPS_API_KEY,
                lat=lat,
                lng=lng,
            )
        return "No coordinates set"
    coordinates_map.short_description = 'Map Preview'

    def quick_stats(self, obj):
        """Display quick location statistics"""
        try:
            from project.models import Project
            projects = Project.objects.filter(location=obj)
            
            stats = {
                'total_projects': projects.count(),
                'active_projects': projects.exclude(status__in=['c', 'm', 'l']).count(),
                'documents': obj.documents.count(),
                'notes': obj.notes.count(),
            }
            
            html = "<table style='font-size: 12px;'>"
            html += f"<tr><td><strong>Total {obj.project_term}:</strong></td><td>{stats['total_projects']}</td></tr>"
            html += f"<tr><td><strong>Active {obj.project_term}:</strong></td><td>{stats['active_projects']}</td></tr>"
            html += f"<tr><td><strong>Documents:</strong></td><td>{stats['documents']}</td></tr>"
            html += f"<tr><td><strong>Notes:</strong></td><td>{stats['notes']}</td></tr>"
            html += "</table>"
            
            return mark_safe(html)
        except:
            return "Statistics unavailable"
    quick_stats.short_description = 'Quick Statistics'

    def project_term_display(self, obj):
        """Show what projects are called for this business type"""
        if obj.business_category:
            return f"Projects are called '{obj.project_term}' for this business type"
        return "Using default 'Projects' terminology"
    project_term_display.short_description = 'Project Terminology'

    def save_model(self, request, obj, form, change):
        """Truncate latitude/longitude to six decimal places before saving."""
        if obj.latitude is not None:
            obj.latitude = obj.latitude.quantize(Decimal('0.000001'), rounding=ROUND_DOWN)
        if obj.longitude is not None:
            obj.longitude = obj.longitude.quantize(Decimal('0.000001'), rounding=ROUND_DOWN)
        super().save_model(request, obj, form, change)

    # Custom actions
    def calculate_contract_values(self, request, queryset):
        """Action to recalculate contract values"""
        updated = 0
        for location in queryset:
            location.calculate_total_contract_value()
            updated += 1
        self.message_user(request, f"Contract values updated for {updated} locations.")
    calculate_contract_values.short_description = "Recalculate contract values"

    def mark_as_active(self, request, queryset):
        """Mark selected locations as active"""
        updated = queryset.update(status='active')
        self.message_user(request, f"{updated} locations marked as active.")
    mark_as_active.short_description = "Mark as active"

    def mark_as_inactive(self, request, queryset):
        """Mark selected locations as inactive"""
        updated = queryset.update(status='inactive')
        self.message_user(request, f"{updated} locations marked as inactive.")
    mark_as_inactive.short_description = "Mark as inactive"

# Location Document Admin
@admin.register(LocationDocument)
class LocationDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'location',
        'document_type',
        'version',
        'is_current',
        'is_public',
        'uploaded_by',
        'created_at'
    )
    
    list_filter = (
        'document_type',
        'is_current',
        'is_public',
        'created_at'
    )
    
    search_fields = (
        'title',
        'description',
        'location__name',
        'location__client__company_name'
    )
    
    readonly_fields = ('created_at', 'updated_at')

# Location Note Admin
@admin.register(LocationNote)
class LocationNoteAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'location',
        'note_type',
        'priority_badge',
        'requires_followup',
        'followup_date',
        'is_client_visible',
        'created_at'
    )
    
    list_filter = (
        'note_type',
        'priority',
        'requires_followup',
        'is_client_visible',
        'created_at'
    )
    
    search_fields = (
        'title',
        'content',
        'location__name',
        'location__client__company_name'
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def priority_badge(self, obj):
        """Display priority with color coding"""
        colors = {
            'low': '#28A745',
            'normal': '#007BFF',
            'high': '#FFA500',
            'urgent': '#DC3545'
        }
        color = colors.get(obj.priority, '#007BFF')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.priority.title()
        )
    priority_badge.short_description = 'Priority'
