from django.contrib import admin

from .models import BusinessConfiguration, TerminologyAlias


class TerminologyAliasInline(admin.TabularInline):
    model = TerminologyAlias
    extra = 0


@admin.register(BusinessConfiguration)
class BusinessConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'deployment_type',
        'billing_model',
        'enables_shared_inventory',
        'enables_shared_workforce',
        'enables_shared_clients',
        'enables_cross_selling',
        'created_at',
    )

    list_filter = (
        'deployment_type',
        'billing_model',
        'enables_shared_inventory',
        'enables_shared_workforce',
        'enables_shared_clients',
        'enables_cross_selling',
        'created_at',
    )

    search_fields = (
        'name',
        'description',
        'industry_details',
    )

    readonly_fields = (
        'slug',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('General', {
            'fields': (
                'name',
                'slug',
                'description',
                'industry_details',
            )
        }),
        ('Business Model', {
            'fields': (
                'deployment_type',
                'billing_model',
            )
        }),
        ('Sharing Capabilities', {
            'fields': (
                'enables_shared_inventory',
                'enables_shared_workforce',
                'enables_shared_clients',
                'enables_cross_selling',
            ),
            'classes': ('collapse',),
        }),
        ('Workflow', {
            'fields': (
                'workflow_requirements',
            ),
            'classes': ('collapse',),
        }),
        ('System Information', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    inlines = [TerminologyAliasInline]


@admin.register(TerminologyAlias)
class TerminologyAliasAdmin(admin.ModelAdmin):
    list_display = ('business_config', 'app_label', 'model', 'field', 'alias')
    list_filter = ('business_config', 'app_label')
    search_fields = ('app_label', 'model', 'field', 'alias')
