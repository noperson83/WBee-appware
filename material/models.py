# material/models.py - Universal Material/Inventory Management Model

from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericRelation
from decimal import Decimal
import uuid

# Import from your modernized apps
from client.models import Address, Contact, TimeStampedModel, UUIDModel
from location.models import BusinessCategory, ConfigurableChoice, get_dynamic_choices
from company.models import Company

class Supplier(UUIDModel, TimeStampedModel):
    """Universal supplier/vendor model (replaces Distributor)"""
    
    # Basic company information
    company_name = models.CharField(max_length=200, db_index=True, help_text='Supplier company name')
    supplier_code = models.CharField(max_length=20, unique=True, help_text='Short code (SUP001, ACME, etc.)')
    
    # Business classification
    SUPPLIER_TYPES = [
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor/Wholesaler'),
        ('retailer', 'Retailer'),
        ('service_provider', 'Service Provider'),
        ('drop_shipper', 'Drop Shipper'),
    ]
    supplier_type = models.CharField(max_length=20, choices=SUPPLIER_TYPES, default='distributor')
    
    # Contact information
    primary_contact_name = models.CharField(max_length=200, blank=True)
    primary_contact_title = models.CharField(max_length=100, blank=True)
    primary_email = models.EmailField(blank=True)
    primary_phone = models.CharField(max_length=17, blank=True)
    
    # Business details
    website = models.URLField(blank=True, help_text='Company website')
    description = models.TextField(max_length=2000, blank=True, help_text='Supplier description')
    
    # Visual branding
    logo = models.ImageField(
        upload_to='uploads/suppliers/logos/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Supplier logo'
    )
    
    # Business terms
    payment_terms = models.CharField(max_length=50, default='Net 30', help_text='Standard payment terms')
    minimum_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Minimum order amount'
    )
    
    # Performance tracking
    PERFORMANCE_RATINGS = [
        (1, '1 - Poor'),
        (2, '2 - Below Average'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]
    quality_rating = models.PositiveIntegerField(
        choices=PERFORMANCE_RATINGS,
        null=True,
        blank=True,
        help_text='Quality rating (1-5 stars)'
    )
    delivery_rating = models.PositiveIntegerField(
        choices=PERFORMANCE_RATINGS,
        null=True,
        blank=True,
        help_text='Delivery rating (1-5 stars)'
    )
    service_rating = models.PositiveIntegerField(
        choices=PERFORMANCE_RATINGS,
        null=True,
        blank=True,
        help_text='Service rating (1-5 stars)'
    )
    
    # Contract information
    contract_details = models.TextField(blank=True, help_text='Contract terms and details')
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    
    # Geographic information
    google_maps_url = models.URLField(blank=True, help_text='Google Maps link to location')
    
    # Related addresses and contacts
    addresses = GenericRelation(Address)
    contacts = GenericRelation(Contact)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_preferred = models.BooleanField(default=False, help_text='Preferred supplier?')
    
    class Meta:
        ordering = ['company_name']
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['supplier_type']),
            models.Index(fields=['is_active', 'is_preferred']),
        ]
    
    def __str__(self):
        return self.company_name
    
    def get_absolute_url(self):
        return reverse('supplier-detail', args=[str(self.id)])
    
    @property
    def primary_address(self):
        """Get the primary address"""
        return self.addresses.filter(is_primary=True, is_active=True).first()
    
    @property
    def average_rating(self):
        """Calculate average rating across all categories"""
        ratings = [r for r in [self.quality_rating, self.delivery_rating, self.service_rating] if r]
        return sum(ratings) / len(ratings) if ratings else 0
    
    @property
    def total_products(self):
        """Get total number of products from this supplier"""
        return self.products.filter(is_active=True).count()

class Manufacturer(UUIDModel, TimeStampedModel):
    """Universal manufacturer model"""
    
    # Basic information
    company_name = models.CharField(max_length=200, db_index=True, help_text='Manufacturer name')
    manufacturer_code = models.CharField(max_length=20, unique=True, help_text='Short code (MFG001, etc.)')
    
    # Contact information
    primary_contact_name = models.CharField(max_length=200, blank=True)
    primary_email = models.EmailField(blank=True)
    primary_phone = models.CharField(max_length=17, blank=True)
    
    # Business details
    website = models.URLField(blank=True)
    description = models.TextField(max_length=2000, blank=True)
    
    # Visual branding
    logo = models.ImageField(
        upload_to='uploads/manufacturers/logos/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Manufacturer logo'
    )
    
    # Quality and certifications
    certifications = models.JSONField(default=list, blank=True, help_text='Quality certifications (ISO, etc.)')
    warranty_terms = models.TextField(blank=True, help_text='Standard warranty terms')
    
    # Relationship with suppliers
    suppliers = models.ManyToManyField(
        Supplier,
        blank=True,
        related_name='manufacturers',
        help_text='Suppliers who carry this manufacturer'
    )
    
    # Related addresses and contacts
    addresses = GenericRelation(Address)
    contacts = GenericRelation(Contact)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['company_name']
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.company_name
    
    @property
    def total_products(self):
        """Get total number of products from this manufacturer"""
        return self.products.filter(is_active=True).count()

class ProductCategory(TimeStampedModel):
    """Configurable product categories for different business types"""
    business_category = models.ForeignKey(
        BusinessCategory,
        on_delete=models.CASCADE,
        related_name='product_categories'
    )
    
    name = models.CharField(max_length=100, help_text='Devices, Wire, Food Items, Medical Supplies, etc.')
    description = models.TextField(blank=True, help_text='Description of this product category')
    icon = models.CharField(max_length=50, blank=True, help_text='Font Awesome icon class')
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    
    # Category settings
    requires_serial_numbers = models.BooleanField(default=False)
    requires_expiration_dates = models.BooleanField(default=False)
    requires_lot_numbers = models.BooleanField(default=False)
    is_billable = models.BooleanField(default=True, help_text='Can items in this category be billed?')
    
    # Inventory settings
    default_unit_of_measure = models.CharField(max_length=20, default='each', help_text='Default UOM')
    track_inventory = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['business_category', 'name']
        unique_together = ['business_category', 'name']
        verbose_name_plural = 'Product Categories'
    
    def __str__(self):
        return f"{self.name} ({self.business_category.name})"

class Product(UUIDModel, TimeStampedModel):
    """Universal product/material model"""
    
    # Basic identification
    sku = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Stock Keeping Unit (unique identifier)'
    )
    
    name = models.CharField(max_length=200, help_text='Product name')
    
    # Classification
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.CASCADE,
        related_name='products'
    )
    
    # Dynamic product type (configurable per business)
    product_type = models.CharField(
        max_length=50,
        help_text='Specific type within category (configurable)'
    )
    
    # Manufacturer and supplier information
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    suppliers = models.ManyToManyField(
        Supplier,
        through='ProductSupplier',
        related_name='products',
        help_text='Suppliers who carry this product'
    )
    
    # Product identification numbers
    manufacturer_part_number = models.CharField(max_length=100, blank=True)
    upc_code = models.CharField(max_length=20, blank=True, help_text='UPC/Barcode')
    internal_part_number = models.CharField(max_length=100, blank=True)
    
    # Description and specifications
    description = models.TextField(blank=True, help_text='Product description')
    specifications = models.JSONField(default=dict, blank=True, help_text='Technical specifications')
    
    # Visual documentation
    primary_image = models.ImageField(
        upload_to='uploads/products/images/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Primary product image'
    )
    
    # Pricing
    cost = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text='Cost per unit'
    )
    
    msrp = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Manufacturer Suggested Retail Price'
    )
    
    markup_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=25.00,
        help_text='Default markup percentage'
    )
    
    # Units and measurements
    UNIT_TYPES = [
        ('each', 'Each'),
        ('box', 'Box'),
        ('case', 'Case'),
        ('foot', 'Foot'),
        ('meter', 'Meter'),
        ('pound', 'Pound'),
        ('kilogram', 'Kilogram'),
        ('liter', 'Liter'),
        ('gallon', 'Gallon'),
        ('hour', 'Hour'),
        ('square_foot', 'Square Foot'),
        ('cubic_foot', 'Cubic Foot'),
    ]
    unit_of_measure = models.CharField(max_length=20, choices=UNIT_TYPES, default='each')
    
    # Package information
    units_per_package = models.PositiveIntegerField(default=1, help_text='Units per package/box')
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Weight per unit'
    )
    weight_unit = models.CharField(max_length=10, default='lbs', help_text='Weight unit')
    
    # Dimensions
    length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dimension_unit = models.CharField(max_length=10, default='inches', help_text='Dimension unit')
    
    # Inventory tracking
    track_inventory = models.BooleanField(default=True)
    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text='Current stock level'
    )
    minimum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text='Minimum stock level (reorder point)'
    )
    maximum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Maximum stock level'
    )
    
    # Quality and compliance
    requires_serial_tracking = models.BooleanField(default=False)
    requires_lot_tracking = models.BooleanField(default=False)
    requires_expiration_tracking = models.BooleanField(default=False)
    shelf_life_days = models.PositiveIntegerField(null=True, blank=True, help_text='Shelf life in days')
    
    # External links
    product_url = models.URLField(blank=True, help_text='Manufacturer product page')
    datasheet_url = models.URLField(blank=True, help_text='Technical datasheet URL')
    installation_guide_url = models.URLField(blank=True, help_text='Installation guide URL')
    
    # Business settings
    is_billable = models.BooleanField(default=True, help_text='Can this product be billed to clients?')
    is_purchasable = models.BooleanField(default=True, help_text='Can this product be purchased?')
    is_sellable = models.BooleanField(default=True, help_text='Can this product be sold?')
    
    # Custom fields for business-specific data
    custom_fields = models.JSONField(default=dict, blank=True, help_text='Custom product data')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_discontinued = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['current_stock']),
            models.Index(fields=['minimum_stock']),
        ]
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    def get_absolute_url(self):
        return reverse('product-detail', args=[str(self.id)])
    
    # Dynamic choice methods
    def get_available_product_types(self):
        """Get available product types for this category"""
        return get_dynamic_choices('product_type', self.category.business_category)
    
    # Pricing calculations
    @property
    def selling_price(self):
        """Calculate selling price with markup"""
        return self.cost * (1 + (self.markup_percentage / 100))
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        selling_price = self.selling_price
        if selling_price > 0:
            return ((selling_price - self.cost) / selling_price) * 100
        return 0
    
    @property
    def is_low_stock(self):
        """Check if product is below minimum stock level"""
        return self.current_stock <= self.minimum_stock
    
    @property
    def is_out_of_stock(self):
        """Check if product is out of stock"""
        return self.current_stock <= 0
    
    @property
    def stock_status(self):
        """Get stock status description"""
        if self.is_out_of_stock:
            return 'out_of_stock'
        elif self.is_low_stock:
            return 'low_stock'
        else:
            return 'in_stock'
    
    # Inventory management
    def adjust_stock(self, quantity, reason="Manual adjustment"):
        """Adjust stock level and create inventory transaction"""
        old_stock = self.current_stock
        self.current_stock += quantity
        self.save()
        
        # Create inventory transaction record
        InventoryTransaction.objects.create(
            product=self,
            transaction_type='adjustment',
            quantity=quantity,
            previous_stock=old_stock,
            new_stock=self.current_stock,
            reason=reason
        )
    
    def receive_stock(self, quantity, supplier=None, cost_per_unit=None):
        """Receive stock from supplier"""
        old_stock = self.current_stock
        self.current_stock += quantity
        
        # Update cost if provided
        if cost_per_unit:
            self.cost = cost_per_unit
        
        self.save()
        
        # Create inventory transaction
        InventoryTransaction.objects.create(
            product=self,
            transaction_type='receipt',
            quantity=quantity,
            previous_stock=old_stock,
            new_stock=self.current_stock,
            supplier=supplier,
            unit_cost=cost_per_unit or self.cost
        )

class ProductSupplier(TimeStampedModel):
    """Junction table for Product-Supplier relationship with pricing"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    
    # Supplier-specific information
    supplier_part_number = models.CharField(max_length=100, blank=True)
    supplier_cost = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        help_text='Cost from this supplier'
    )
    
    # Ordering information
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    lead_time_days = models.PositiveIntegerField(default=7, help_text='Lead time in days')
    
    # Supplier performance for this product
    last_order_date = models.DateField(null=True, blank=True)
    total_orders = models.PositiveIntegerField(default=0)
    
    # Status
    is_primary_supplier = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['product', 'supplier']
        ordering = ['-is_primary_supplier', 'supplier_cost']
    
    def __str__(self):
        return f"{self.product.name} from {self.supplier.company_name}"

class InventoryTransaction(TimeStampedModel):
    """Track all inventory movements"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    
    TRANSACTION_TYPES = [
        ('receipt', 'Stock Receipt'),
        ('issue', 'Stock Issue/Usage'),
        ('adjustment', 'Stock Adjustment'),
        ('transfer', 'Transfer'),
        ('return', 'Return'),
        ('write_off', 'Write-off'),
    ]
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    
    # Quantity and stock levels
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    previous_stock = models.DecimalField(max_digits=12, decimal_places=4)
    new_stock = models.DecimalField(max_digits=12, decimal_places=4)
    
    # Financial information
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    total_value = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    
    # Related information
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True, help_text='PO number, invoice number, etc.')
    reason = models.CharField(max_length=200, blank=True, help_text='Reason for transaction')
    
    # User tracking
    created_by = models.CharField(max_length=100, blank=True, help_text='Who created this transaction')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'transaction_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} ({self.quantity})"

# Default data creation functions
def create_default_product_categories():
    """Create default product categories for different business types"""
    
    from location.models import BusinessCategory
    
    try:
        # Get business categories
        construction = BusinessCategory.objects.get(name='Construction & AV')
        distribution = BusinessCategory.objects.get(name='Distribution & Logistics')
        entertainment = BusinessCategory.objects.get(name='Entertainment')
        healthcare = BusinessCategory.objects.get(name='Healthcare Services')
        food_beverage = BusinessCategory.objects.get(name='Food & Beverage')
        
        # Construction product categories
        construction_categories = [
            ('Devices & Equipment', 'fas fa-microchip', '#007bff', False, False, False),
            ('Wire & Cable', 'fas fa-ethernet', '#28a745', False, False, False),
            ('Hardware & Mounting', 'fas fa-screwdriver', '#6f42c1', False, False, False),
            ('Software & Licenses', 'fas fa-code', '#fd7e14', True, True, False),
            ('Tools & Instruments', 'fas fa-tools', '#dc3545', True, False, False),
        ]
        
        # Distribution categories
        distribution_categories = [
            ('Beverages', 'fas fa-wine-bottle', '#e83e8c', False, True, True),
            ('Food Products', 'fas fa-apple-alt', '#28a745', False, True, True),
            ('Packaging Materials', 'fas fa-box', '#6f42c1', False, False, False),
            ('Promotional Items', 'fas fa-tags', '#ffc107', False, False, False),
        ]
        
        # Entertainment categories
        entertainment_categories = [
            ('Audio Equipment', 'fas fa-volume-up', '#e83e8c', True, False, False),
            ('Lighting Equipment', 'fas fa-lightbulb', '#ffc107', True, False, False),
            ('Stage Materials', 'fas fa-theater-masks', '#6f42c1', False, False, False),
            ('Instruments & Accessories', 'fas fa-guitar', '#fd7e14', True, False, False),
        ]
        
        # Healthcare categories
        healthcare_categories = [
            ('Medical Supplies', 'fas fa-prescription-bottle', '#dc3545', False, True, True),
            ('Equipment & Devices', 'fas fa-stethoscope', '#007bff', True, False, False),
            ('Pharmaceuticals', 'fas fa-pills', '#28a745', True, True, True),
            ('Personal Care Items', 'fas fa-hand-holding-heart', '#17a2b8', False, True, False),
        ]
        
        # Food & Beverage categories
        food_categories = [
            ('Ingredients', 'fas fa-leaf', '#28a745', False, True, True),
            ('Beverages', 'fas fa-coffee', '#6f42c1', False, True, False),
            ('Kitchen Supplies', 'fas fa-utensils', '#fd7e14', False, False, False),
            ('Serving Items', 'fas fa-wine-glass', '#e83e8c', False, False, False),
        ]
        
        # Create product categories
        for category, categories_list in [
            (construction, construction_categories),
            (distribution, distribution_categories),
            (entertainment, entertainment_categories),
            (healthcare, healthcare_categories),
            (food_beverage, food_categories)
        ]:
            for name, icon, color, serial_req, exp_req, lot_req in categories_list:
                ProductCategory.objects.get_or_create(
                    business_category=category,
                    name=name,
                    defaults={
                        'icon': icon,
                        'color': color,
                        'requires_serial_numbers': serial_req,
                        'requires_expiration_dates': exp_req,
                        'requires_lot_numbers': lot_req
                    }
                )
        
        print("Default product categories created successfully!")
        
    except BusinessCategory.DoesNotExist:
        print("Business categories not found. Please run location data creation first.")