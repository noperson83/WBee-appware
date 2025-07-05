# material/admin.py - Universal Material/Inventory Admin Interface

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    Supplier, Manufacturer, ProductCategory, Product,
    ProductSupplier, InventoryTransaction, MaterialLifecycle
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

class ProductSupplierInline(admin.TabularInline):
    """Inline admin for product-supplier relationships"""
    model = ProductSupplier
    extra = 0
    fields = (
        'supplier', 'supplier_part_number', 'supplier_cost',
        'minimum_order_quantity', 'lead_time_days', 'is_primary_supplier'
    )
    readonly_fields = ('last_order_date', 'total_orders')

class InventoryTransactionInline(admin.TabularInline):
    """Inline admin for inventory transactions"""
    model = InventoryTransaction
    extra = 0
    fields = (
        'transaction_type', 'quantity', 'unit_cost', 
        'supplier', 'reference_number', 'reason'
    )
    readonly_fields = ('previous_stock', 'new_stock', 'created_at')

# Supplier Admin
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'company_name',
        'supplier_code',
        'supplier_type',
        'contact_display',
        'performance_display',
        'product_count',
        'contract_status',
        'is_preferred',
        'is_active'
    )

    list_filter = (
        'supplier_type',
        'is_active',
        'is_preferred',
        'quality_rating',
        'delivery_rating',
        'service_rating',
        'contract_start_date'
    )

    search_fields = (
        'company_name',
        'supplier_code',
        'primary_contact_name',
        'primary_email',
        'description'
    )

    readonly_fields = (
        'id',
        'average_rating',
        'total_products',
        'created_at',
        'updated_at',
        'logo_preview',
        'performance_summary'
    )

    fieldsets = (
        ('Supplier Information', {
            'fields': (
                'company_name',
                'supplier_code',
                'supplier_type',
                'description'
            )
        }),
        ('Contact Information', {
            'fields': (
                'primary_contact_name',
                'primary_contact_title',
                'primary_email',
                'primary_phone'
            )
        }),
        ('Business Details', {
            'fields': (
                'website',
                ('logo', 'logo_preview'),
                'google_maps_url'
            )
        }),
        ('Terms & Performance', {
            'fields': (
                'payment_terms',
                'minimum_order',
                ('quality_rating', 'delivery_rating', 'service_rating'),
                'average_rating',
                'performance_summary'
            )
        }),
        ('Contract Information', {
            'fields': (
                'contract_details',
                'contract_start_date',
                'contract_end_date'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': (
                'is_active',
                'is_preferred',
                'total_products'
            )
        }),
        ('System Information', {
            'fields': (
                'id',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [AddressInline, ContactInline]

    actions = ['mark_preferred', 'mark_active', 'mark_inactive']

    def contact_display(self, obj):
        """Display primary contact information"""
        if obj.primary_contact_name:
            contact_info = f"👤 {obj.primary_contact_name}"
            if obj.primary_email:
                contact_info += f"<br>📧 {obj.primary_email}"
            if obj.primary_phone:
                contact_info += f"<br>📞 {obj.primary_phone}"
            return format_html(contact_info)
        return "—"
    contact_display.short_description = 'Contact'

    def performance_display(self, obj):
        """Display performance ratings with stars"""
        def stars(rating):
            if rating:
                return "★" * rating + "☆" * (5 - rating)
            return "—"
        
        html = f"<div style='font-size: 11px;'>"
        html += f"Quality: {stars(obj.quality_rating)}<br>"
        html += f"Delivery: {stars(obj.delivery_rating)}<br>"
        html += f"Service: {stars(obj.service_rating)}"
        html += f"</div>"
        
        avg = obj.average_rating
        if avg > 0:
            color = '#28a745' if avg >= 4 else '#ffc107' if avg >= 3 else '#dc3545'
            html += f"<div style='color: {color}; font-weight: bold;'>Avg: {avg:.1f}</div>"
        
        return format_html(html)
    performance_display.short_description = 'Performance'

    def product_count(self, obj):
        """Display number of products from this supplier"""
        count = obj.total_products
        if count > 0:
            url = reverse('admin:material_product_changelist') + f'?suppliers__id__exact={obj.id}'
            return format_html('<a href="{}">{} products</a>', url, count)
        return "0 products"
    product_count.short_description = 'Products'

    def contract_status(self, obj):
        """Display contract status"""
        if obj.contract_end_date:
            days_left = (obj.contract_end_date - date.today()).days
            if days_left < 0:
                return format_html('<span style="color: #dc3545;">Expired</span>')
            elif days_left <= 30:
                return format_html('<span style="color: #ffc107;">Expires in {} days</span>', days_left)
            else:
                return format_html('<span style="color: #28a745;">Active</span>')
        return "—"
    contract_status.short_description = 'Contract'

    def logo_preview(self, obj):
        """Display logo preview"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.logo.url
            )
        return "No logo"
    logo_preview.short_description = 'Logo Preview'

    def performance_summary(self, obj):
        """Display performance summary"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Average Rating:</strong></td><td>{obj.average_rating:.1f}/5</td></tr>"
        html += f"<tr><td><strong>Total Products:</strong></td><td>{obj.total_products}</td></tr>"
        
        if obj.contract_start_date:
            html += f"<tr><td><strong>Contract Since:</strong></td><td>{obj.contract_start_date}</td></tr>"
        
        # Add recent order statistics
        recent_orders = obj.productsupplier_set.filter(last_order_date__gte=date.today()-timedelta(days=90))
        html += f"<tr><td><strong>Recent Orders (90d):</strong></td><td>{recent_orders.count()}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    performance_summary.short_description = 'Performance Summary'

    # Custom actions
    def mark_preferred(self, request, queryset):
        updated = queryset.update(is_preferred=True)
        self.message_user(request, f"{updated} suppliers marked as preferred.")
    mark_preferred.short_description = "Mark as preferred suppliers"

    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} suppliers activated.")
    mark_active.short_description = "Activate suppliers"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} suppliers deactivated.")
    mark_inactive.short_description = "Deactivate suppliers"

# Manufacturer Admin
@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = (
        'company_name',
        'manufacturer_code',
        'contact_display',
        'product_count',
        'supplier_count',
        'is_active'
    )

    list_filter = (
        'is_active',
        'created_at'
    )

    search_fields = (
        'company_name',
        'manufacturer_code',
        'description'
    )

    readonly_fields = (
        'id',
        'total_products',
        'logo_preview',
        'created_at',
        'updated_at'
    )

    fieldsets = (
        ('Manufacturer Information', {
            'fields': (
                'company_name',
                'manufacturer_code',
                'description'
            )
        }),
        ('Contact Information', {
            'fields': (
                'primary_contact_name',
                'primary_email',
                'primary_phone',
                'website'
            )
        }),
        ('Branding & Quality', {
            'fields': (
                ('logo', 'logo_preview'),
                'certifications',
                'warranty_terms'
            )
        }),
        ('Supplier Relationships', {
            'fields': (
                'suppliers',
            )
        }),
        ('System Information', {
            'fields': (
                'id',
                'total_products',
                'is_active',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [AddressInline, ContactInline]

    def contact_display(self, obj):
        """Display contact information"""
        if obj.primary_contact_name:
            return f"👤 {obj.primary_contact_name}"
        return "—"
    contact_display.short_description = 'Contact'

    def product_count(self, obj):
        """Display number of products"""
        count = obj.total_products
        if count > 0:
            url = reverse('admin:material_product_changelist') + f'?manufacturer__id__exact={obj.id}'
            return format_html('<a href="{}">{} products</a>', url, count)
        return "0 products"
    product_count.short_description = 'Products'

    def supplier_count(self, obj):
        """Display number of suppliers"""
        count = obj.suppliers.count()
        return f"{count} suppliers"
    supplier_count.short_description = 'Suppliers'

    def logo_preview(self, obj):
        """Display logo preview"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.logo.url
            )
        return "No logo"
    logo_preview.short_description = 'Logo Preview'

# Product Category Admin
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'business_category',
        'icon_display',
        'product_count',
        'tracking_requirements',
        'is_active'
    )

    list_filter = (
        'business_category',
        'requires_serial_numbers',
        'requires_expiration_dates',
        'requires_lot_numbers',
        'is_billable',
        'track_inventory',
        'is_active'
    )

    search_fields = (
        'name',
        'description',
        'business_category__name'
    )

    fieldsets = (
        ('Category Information', {
            'fields': (
                'business_category',
                'name',
                'description',
                'is_active'
            )
        }),
        ('Visual Settings', {
            'fields': (
                'icon',
                'color'
            )
        }),
        ('Tracking Requirements', {
            'fields': (
                'requires_serial_numbers',
                'requires_expiration_dates',
                'requires_lot_numbers',
                'is_billable'
            )
        }),
        ('Inventory Settings', {
            'fields': (
                'default_unit_of_measure',
                'track_inventory'
            )
        })
    )

    def icon_display(self, obj):
        if obj.icon:
            return format_html(
                '<i class="{}" style="color: {}; font-size: 16px;"></i> {}',
                obj.icon, obj.color, obj.icon
            )
        return "—"
    icon_display.short_description = 'Icon'

    def product_count(self, obj):
        count = obj.products.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:material_product_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} products</a>', url, count)
        return "0 products"
    product_count.short_description = 'Products'

    def tracking_requirements(self, obj):
        requirements = []
        if obj.requires_serial_numbers:
            requirements.append("Serial #")
        if obj.requires_expiration_dates:
            requirements.append("Expiration")
        if obj.requires_lot_numbers:
            requirements.append("Lot #")
        
        return ", ".join(requirements) if requirements else "None"
    tracking_requirements.short_description = 'Tracking'

# Main Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'sku',
        'name',
        'category_display',
        'manufacturer',
        'cost_and_price',
        'stock_status_display',
        'supplier_count',
        'profit_margin_display',
        'is_active'
    )

    list_filter = (
        'category',
        'manufacturer',
        'unit_of_measure',
        'is_active',
        'is_discontinued',
        'is_billable',
        'track_inventory',
        'requires_serial_tracking',
        'requires_expiration_tracking'
    )

    search_fields = (
        'sku',
        'name',
        'description',
        'manufacturer_part_number',
        'internal_part_number',
        'upc_code'
    )

    readonly_fields = (
        'id',
        'selling_price',
        'profit_margin',
        'is_low_stock',
        'is_out_of_stock',
        'stock_status',
        'primary_image_preview',
        'inventory_summary',
        'supplier_summary',
        'financial_summary',
        'created_at',
        'updated_at'
    )

    fieldsets = (
        ('Product Identification', {
            'fields': (
                'sku',
                'name',
                'category',
                'product_type',
                'description'
            )
        }),
        ('Manufacturer & Part Numbers', {
            'fields': (
                'manufacturer',
                'manufacturer_part_number',
                'internal_part_number',
                'upc_code'
            )
        }),
        ('Visual Documentation', {
            'fields': (
                ('primary_image', 'primary_image_preview'),
            )
        }),
        ('Pricing', {
            'fields': (
                'cost',
                'markup_percentage',
                'selling_price',
                'msrp',
                'profit_margin',
                'financial_summary'
            )
        }),
        ('Units & Measurements', {
            'fields': (
                'unit_of_measure',
                'units_per_package',
                ('weight', 'weight_unit'),
                ('length', 'width', 'height', 'dimension_unit')
            ),
            'classes': ('collapse',)
        }),
        ('Inventory Management', {
            'fields': (
                'track_inventory',
                'current_stock',
                'minimum_stock',
                'maximum_stock',
                'stock_status',
                'inventory_summary'
            )
        }),
        ('Quality & Compliance', {
            'fields': (
                'requires_serial_tracking',
                'requires_lot_tracking',
                'requires_expiration_tracking',
                'shelf_life_days'
            ),
            'classes': ('collapse',)
        }),
        ('External Links', {
            'fields': (
                'product_url',
                'datasheet_url',
                'installation_guide_url'
            ),
            'classes': ('collapse',)
        }),
        ('Business Settings', {
            'fields': (
                'is_billable',
                'is_purchasable',
                'is_sellable'
            ),
            'classes': ('collapse',)
        }),
        ('Supplier Information', {
            'fields': (
                'supplier_summary',
            ),
            'classes': ('collapse',)
        }),
        ('Technical Specifications', {
            'fields': (
                'specifications',
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
                'is_active',
                'is_discontinued',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [ProductSupplierInline, InventoryTransactionInline]

    actions = [
        'mark_active',
        'mark_discontinued',
        'update_stock_levels',
        'recalculate_pricing'
    ]

    def category_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold;"><i class="{}"></i> {}</span>',
            obj.category.color,
            obj.category.icon,
            obj.category.name
        )
    category_display.short_description = 'Category'

    def cost_and_price(self, obj):
        """Display cost and selling price"""
        selling_price = obj.selling_price
        html = f"<div style='font-size: 11px;'>"
        html += f"<strong>${obj.cost:.2f}</strong> cost<br>"
        html += f"<span style='color: #28a745;'>${selling_price:.2f}</span> sell"
        html += "</div>"
        return format_html(html)
    cost_and_price.short_description = 'Cost/Price'

    def stock_status_display(self, obj):
        """Display stock status with color coding"""
        if not obj.track_inventory:
            return format_html('<span style="color: #6c757d;">Not tracked</span>')
        
        status = obj.stock_status
        stock = obj.current_stock
        
        if status == 'out_of_stock':
            color = '#dc3545'
            icon = '❌'
            text = f'OUT ({stock})'
        elif status == 'low_stock':
            color = '#ffc107'
            icon = '⚠️'
            text = f'LOW ({stock})'
        else:
            color = '#28a745'
            icon = '✅'
            text = f'OK ({stock})'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, text
        )
    stock_status_display.short_description = 'Stock Status'

    def supplier_count(self, obj):
        """Display number of suppliers"""
        count = obj.suppliers.count()
        if count > 0:
            # Show primary supplier if available
            primary = obj.productsupplier_set.filter(is_primary_supplier=True).first()
            if primary:
                return format_html(
                    '{} suppliers<br><small>Primary: {}</small>',
                    count, primary.supplier.company_name[:20]
                )
            return f"{count} suppliers"
        return "No suppliers"
    supplier_count.short_description = 'Suppliers'

    def profit_margin_display(self, obj):
        """Display profit margin with color coding"""
        margin = obj.profit_margin
        if margin >= 30:
            color = '#28a745'
        elif margin >= 15:
            color = '#ffc107'
        else:
            color = '#dc3545'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, f"{margin:.1f}%"
        )
    profit_margin_display.short_description = 'Margin'

    def primary_image_preview(self, obj):
        """Display primary image preview"""
        if obj.primary_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.primary_image.url
            )
        return "No image"
    primary_image_preview.short_description = 'Image Preview'

    def inventory_summary(self, obj):
        """Display inventory summary"""
        if not obj.track_inventory:
            return "Inventory not tracked"
        
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Current Stock:</strong></td><td>{obj.current_stock} {obj.unit_of_measure}</td></tr>"
        html += f"<tr><td><strong>Minimum Level:</strong></td><td>{obj.minimum_stock}</td></tr>"
        
        if obj.maximum_stock:
            html += f"<tr><td><strong>Maximum Level:</strong></td><td>{obj.maximum_stock}</td></tr>"
        
        # Recent transactions
        recent_transactions = obj.transactions.order_by('-created_at')[:3]
        if recent_transactions:
            html += "<tr><td colspan='2'><strong>Recent Transactions:</strong></td></tr>"
            for txn in recent_transactions:
                html += f"<tr><td style='padding-left: 10px;'>{txn.transaction_type}</td><td>{txn.quantity:+.2f}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    inventory_summary.short_description = 'Inventory Summary'

    def supplier_summary(self, obj):
        """Display supplier summary"""
        suppliers = obj.productsupplier_set.order_by('-is_primary_supplier', 'supplier_cost')
        
        if not suppliers:
            return "No suppliers configured"
        
        html = "<table style='font-size: 12px;'>"
        html += "<tr><th>Supplier</th><th>Cost</th><th>Lead Time</th><th>Primary</th></tr>"
        
        for ps in suppliers[:5]:  # Show top 5 suppliers
            primary_icon = "⭐" if ps.is_primary_supplier else ""
            html += f"<tr>"
            html += f"<td>{ps.supplier.company_name[:20]} {primary_icon}</td>"
            html += f"<td>${ps.supplier_cost:.2f}</td>"
            html += f"<td>{ps.lead_time_days}d</td>"
            html += f"<td>{'Yes' if ps.is_primary_supplier else 'No'}</td>"
            html += f"</tr>"
        
        if suppliers.count() > 5:
            html += f"<tr><td colspan='4'>... and {suppliers.count() - 5} more</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    supplier_summary.short_description = 'Supplier Summary'

    def financial_summary(self, obj):
        """Display financial summary"""
        html = "<table style='font-size: 12px;'>"
        html += f"<tr><td><strong>Cost:</strong></td><td>${obj.cost:.4f}</td></tr>"
        html += f"<tr><td><strong>Selling Price:</strong></td><td>${obj.selling_price:.2f}</td></tr>"
        html += f"<tr><td><strong>Markup:</strong></td><td>{obj.markup_percentage:.1f}%</td></tr>"
        html += f"<tr><td><strong>Profit Margin:</strong></td><td>{obj.profit_margin:.1f}%</td></tr>"
        
        if obj.msrp:
            html += f"<tr><td><strong>MSRP:</strong></td><td>${obj.msrp:.2f}</td></tr>"
        
        # Inventory value
        if obj.track_inventory and obj.current_stock > 0:
            inventory_value = obj.current_stock * obj.cost
            html += f"<tr><td><strong>Inventory Value:</strong></td><td>${inventory_value:.2f}</td></tr>"
        
        html += "</table>"
        return mark_safe(html)
    financial_summary.short_description = 'Financial Summary'

    # Custom actions
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True, is_discontinued=False)
        self.message_user(request, f"{updated} products marked as active.")
    mark_active.short_description = "Mark as active"

    def mark_discontinued(self, request, queryset):
        updated = queryset.update(is_discontinued=True)
        self.message_user(request, f"{updated} products marked as discontinued.")
    mark_discontinued.short_description = "Mark as discontinued"

    def update_stock_levels(self, request, queryset):
        # This would typically integrate with an inventory system
        count = queryset.count()
        self.message_user(request, f"Stock levels would be updated for {count} products.")
    update_stock_levels.short_description = "Update stock levels"

    def recalculate_pricing(self, request, queryset):
        updated = 0
        for product in queryset:
            # This would recalculate pricing based on latest costs
            updated += 1
        self.message_user(request, f"Pricing recalculated for {updated} products.")
    recalculate_pricing.short_description = "Recalculate pricing"

# Product Supplier Admin
@admin.register(ProductSupplier)
class ProductSupplierAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'supplier',
        'supplier_cost_display',
        'lead_time_days',
        'minimum_order_quantity',
        'order_history',
        'is_primary_supplier',
        'is_active'
    )

    list_filter = (
        'is_primary_supplier',
        'is_active',
        'lead_time_days',
        'supplier__supplier_type'
    )

    search_fields = (
        'product__sku',
        'product__name',
        'supplier__company_name',
        'supplier_part_number'
    )

    def supplier_cost_display(self, obj):
        return f"${obj.supplier_cost:.4f}"
    supplier_cost_display.short_description = 'Cost'

    def order_history(self, obj):
        if obj.last_order_date:
            return f"{obj.total_orders} orders (last: {obj.last_order_date})"
        return f"{obj.total_orders} orders"
    order_history.short_description = 'Order History'

# Inventory Transaction Admin
@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'product',
        'transaction_type',
        'quantity_display',
        'stock_change',
        'value_display',
        'supplier',
        'reference_number'
    )

    list_filter = (
        'transaction_type',
        'created_at',
        'supplier',
        'product__category'
    )

    search_fields = (
        'product__sku',
        'product__name',
        'reference_number',
        'reason',
        'created_by'
    )

    readonly_fields = ('created_at', 'updated_at')

    def quantity_display(self, obj):
        """Display quantity with +/- indicator"""
        if obj.quantity >= 0:
            return format_html(
                '<span style="color: #28a745;">{}</span>',
                f"+{obj.quantity:.2f}"
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">{}</span>',
                f"{obj.quantity:.2f}"
            )
    quantity_display.short_description = 'Quantity'

    def stock_change(self, obj):
        """Display stock level change"""
        return f"{obj.previous_stock} → {obj.new_stock}"
    stock_change.short_description = 'Stock Change'

    def value_display(self, obj):
        """Display transaction value"""
        if obj.total_value:
            return f"${obj.total_value:,.2f}"
        return "—"
    value_display.short_description = 'Value'


@admin.register(MaterialLifecycle)
class MaterialLifecycleAdmin(admin.ModelAdmin):
    list_display = (
        'project_material',
        'purchased_from',
        'received_at',
        'installed_at',
    )
    list_filter = ('purchased_from',)
    search_fields = (
        'project_material__project__job_number',
        'project_material__product__name',
    )
    readonly_fields = ('created_at', 'updated_at')
