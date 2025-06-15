from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Receipt, PurchaseType


@admin.register(PurchaseType)
class PurchaseTypeAdmin(admin.ModelAdmin):
    """
    Admin configuration for PurchaseType model.
    """
    list_display = ['name', 'code', 'is_active', 'receipt_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def receipt_count(self, obj):
        """Display the number of receipts using this purchase type."""
        count = obj.receipts.count()
        if count > 0:
            url = reverse('admin:receipts_receipt_changelist') + f'?purchase_type__id__exact={obj.id}'
            return format_html('<a href="{}">{} receipts</a>', url, count)
        return '0 receipts'
    receipt_count.short_description = 'Receipts'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch for receipt counts."""
        return super().get_queryset(request).prefetch_related('receipts')


class ReceiptImageMixin:
    """Mixin for displaying receipt images in admin."""
    
    def receipt_image_preview(self, obj):
        """Display a small preview of the receipt image."""
        if obj.receipt_image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.receipt_image.url
            )
        return "No image"
    receipt_image_preview.short_description = 'Image'


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin, ReceiptImageMixin):
    """
    Admin configuration for Receipt model with enhanced functionality.
    """
    list_display = [
        'date_of_purchase', 
        'company_name', 
        'project_link',
        'worker_name',
        'purchase_type',
        'total_amount',
        'is_reimbursed',
        'receipt_image_preview',
        'is_recent_badge'
    ]
    
    list_filter = [
        'is_reimbursed',
        'purchase_type',
        'date_of_purchase',
        ('project', admin.RelatedOnlyFieldListFilter),
        ('worker', admin.RelatedOnlyFieldListFilter),
        'created_at',
    ]
    
    search_fields = [
        'company_name',
        'description',
        'notes',
        'project__job_num',
        'project__name',
        'worker__first_name',
        'worker__last_name',
    ]
    
    date_hierarchy = 'date_of_purchase'
    
    ordering = ['-date_of_purchase', '-created_at']
    
    fieldsets = (
        ('Purchase Information', {
            'fields': (
                ('date_of_purchase', 'company_name'),
                ('project', 'worker'),
                'purchase_type',
                'total_amount',
                'description',
            )
        }),
        ('Receipt Documentation', {
            'fields': ('receipt_image', 'notes'),
        }),
        ('Reimbursement Tracking', {
            'fields': (
                ('is_reimbursed', 'reimbursement_date'),
            ),
            'classes': ('collapse',),
        }),
        ('System Information', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    list_per_page = 25
    
    actions = [
        'mark_as_reimbursed',
        'mark_as_not_reimbursed',
        'export_selected_receipts',
    ]
    
    # Custom display methods
    def project_link(self, obj):
        """Display project with link to project admin."""
        if obj.project:
            url = reverse('admin:project_project_change', args=[obj.project.id])
            return format_html('<a href="{}">{}</a>', url, obj.project)
        return "No project"
    project_link.short_description = 'Project'
    project_link.admin_order_field = 'project__job_num'
    
    def worker_name(self, obj):
        """Display worker name with link."""
        if obj.worker:
            url = reverse('admin:hr_worker_change', args=[obj.worker.id])
            return format_html('<a href="{}">{}</a>', url, obj.worker)
        return "No worker"
    worker_name.short_description = 'Worker'
    worker_name.admin_order_field = 'worker__last_name'
    
    def is_recent_badge(self, obj):
        """Display a badge for recent receipts."""
        if obj.is_recent:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 2px 6px; '
                'border-radius: 3px; font-size: 11px;">Recent</span>'
            )
        return ""
    is_recent_badge.short_description = 'Status'
    
    # Custom actions
    def mark_as_reimbursed(self, request, queryset):
        """Mark selected receipts as reimbursed."""
        updated = queryset.update(
            is_reimbursed=True,
            reimbursement_date=timezone.now().date()
        )
        self.message_user(
            request,
            f'{updated} receipts marked as reimbursed.'
        )
    mark_as_reimbursed.short_description = "Mark selected receipts as reimbursed"
    
    def mark_as_not_reimbursed(self, request, queryset):
        """Mark selected receipts as not reimbursed."""
        updated = queryset.update(
            is_reimbursed=False,
            reimbursement_date=None
        )
        self.message_user(
            request,
            f'{updated} receipts marked as not reimbursed.'
        )
    mark_as_not_reimbursed.short_description = "Mark selected receipts as not reimbursed"
    
    def export_selected_receipts(self, request, queryset):
        """Export selected receipts to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="receipts_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Company', 'Project', 'Worker', 'Type', 
            'Amount', 'Description', 'Reimbursed', 'Notes'
        ])
        
        for receipt in queryset:
            writer.writerow([
                receipt.date_of_purchase,
                receipt.company_name,
                receipt.project.job_num if receipt.project else '',
                str(receipt.worker) if receipt.worker else '',
                receipt.purchase_type.name,
                receipt.total_amount,
                receipt.description,
                'Yes' if receipt.is_reimbursed else 'No',
                receipt.notes,
            ])
        
        return response
    export_selected_receipts.short_description = "Export selected receipts to CSV"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related(
            'project', 'worker', 'purchase_type'
        )
    
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to the changelist view."""
        queryset = self.get_queryset(request)
        
        # Apply any filters from the request
        cl = self.get_changelist_instance(request)
        queryset = cl.get_queryset(request)
        
        # Calculate summary statistics
        summary = queryset.aggregate(
            total_amount=Sum('total_amount'),
            total_count=Count('id'),
            reimbursed_count=Count('id', filter=models.Q(is_reimbursed=True)),
            recent_count=Count('id', filter=models.Q(
                date_of_purchase__gte=timezone.now().date() - timedelta(days=30)
            ))
        )
        
        extra_context = extra_context or {}
        extra_context['summary'] = summary
        
        return super().changelist_view(request, extra_context=extra_context)


# Admin site customization
admin.site.site_header = "Company Manager - Receipts"
admin.site.site_title = "Receipts Admin"
admin.site.index_title = "Welcome to Receipts Administration"
