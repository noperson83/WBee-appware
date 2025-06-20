# helpdesk/models/customfields.py - Custom Fields and Values

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class CustomFieldManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by('ordering')

    def active(self):
        """Get active custom fields only"""
        return self.filter(is_active=True)

    def for_staff_only(self):
        """Get staff-only fields"""
        return self.filter(staff_only=True, is_active=True)

    def public_fields(self):
        """Get fields visible to public"""
        return self.filter(staff_only=False, is_active=True)

class CustomField(models.Model):
    """
    Enhanced custom fields with better validation and organization
    """
    DATA_TYPE_CHOICES = [
        ('varchar', _('Character (single line)')),
        ('text', _('Text (multi-line)')),
        ('integer', _('Integer')),
        ('decimal', _('Decimal')),
        ('list', _('List')),
        ('boolean', _('Boolean (checkbox yes/no)')),
        ('date', _('Date')),
        ('time', _('Time')),
        ('datetime', _('Date & Time')),
        ('email', _('E-Mail Address')),
        ('url', _('URL')),
        ('ipaddress', _('IP Address')),
        ('slug', _('Slug')),
        ('file', _('File Upload')),
        ('json', _('JSON Data')),
    ]

    FIELD_GROUPS = [
        ('basic', _('Basic Information')),
        ('technical', _('Technical Details')),
        ('business', _('Business Information')),
        ('custom', _('Custom Fields')),
    ]

    # Basic Information
    name = models.SlugField(
        _('Field Name'),
        help_text=_('As used in the database and behind the scenes. Must be unique and consist of only lowercase letters with no punctuation.'),
        unique=True
    )
    label = models.CharField(
        _('Label'),
        max_length=100,
        help_text=_('The display label for this field')
    )
    help_text = models.TextField(
        _('Help Text'),
        help_text=_('Shown to the user when editing the ticket'),
        blank=True,
        null=True
    )
    placeholder = models.CharField(
        _('Placeholder'),
        max_length=100,
        blank=True,
        help_text=_('Placeholder text shown in the input field')
    )

    # Field Configuration
    data_type = models.CharField(
        _('Data Type'),
        max_length=100,
        help_text=_('Allows you to restrict the data entered into this field'),
        choices=DATA_TYPE_CHOICES
    )
    field_group = models.CharField(
        _('Field Group'),
        max_length=20,
        choices=FIELD_GROUPS,
        default='custom',
        help_text=_('Group this field belongs to for organization')
    )

    # Validation
    max_length = models.IntegerField(
        _('Maximum Length (characters)'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(10000)]
    )
    decimal_places = models.IntegerField(
        _('Decimal Places'),
        help_text=_('Only used for decimal fields'),
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    min_value = models.DecimalField(
        _('Minimum Value'),
        max_digits=15,
        decimal_places=5,
        blank=True,
        null=True,
        help_text=_('Minimum value for numeric fields')
    )
    max_value = models.DecimalField(
        _('Maximum Value'),
        max_digits=15,
        decimal_places=5,
        blank=True,
        null=True,
        help_text=_('Maximum value for numeric fields')
    )

    # List Configuration
    empty_selection_list = models.BooleanField(
        _('Add empty first choice to List?'),
        default=False,
        help_text=_('Only for List: adds an empty first entry to the choices list, which enforces that the user makes an active choice.')
    )
    list_values = models.TextField(
        _('List Values'),
        help_text=_('For list fields only. Enter one option per line.'),
        blank=True,
        null=True
    )
    allow_multiple = models.BooleanField(
        _('Allow Multiple Selections'),
        default=False,
        help_text=_('For list fields: allow multiple selections')
    )

    # Display and Behavior
    ordering = models.IntegerField(
        _('Ordering'),
        help_text=_('Lower numbers are displayed first; higher numbers are listed later'),
        default=0
    )
    required = models.BooleanField(
        _('Required?'),
        help_text=_('Does the user have to enter a value for this field?'),
        default=False
    )
    staff_only = models.BooleanField(
        _('Staff Only?'),
        help_text=_('If this is ticked, then the public submission form will NOT show this field'),
        default=False
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this field is currently available for use')
    )

    # Queue Assignment
    queues = models.ManyToManyField(
        'base.Queue',
        blank=True,
        help_text=_('Leave blank to use for all queues, or select specific queues')
    )

    objects = CustomFieldManager()

    class Meta:
        verbose_name = _('Custom field')
        verbose_name_plural = _('Custom fields')
        ordering = ['field_group', 'ordering', 'label']

    def __str__(self):
        return f'{self.label} ({self.name})'

    @property
    def choices_as_array(self):
        """Convert list values to array format"""
        if not self.list_values:
            return []
        
        choices = []
        for line in self.list_values.splitlines():
            line = line.strip()
            if line:
                if '|' in line:
                    # Support value|label format
                    value, label = line.split('|', 1)
                    choices.append([value.strip(), label.strip()])
                else:
                    choices.append([line, line])
        return choices

class TicketCustomFieldValue(models.Model):
    """
    Enhanced custom field values with better data handling
    """
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='custom_field_values',
        verbose_name=_('Ticket')
    )
    field = models.ForeignKey(
        CustomField,
        on_delete=models.CASCADE,
        verbose_name=_('Field')
    )
    value = models.TextField(blank=True, null=True)
    
    # Enhanced value storage for different data types
    value_text = models.TextField(_('Text Value'), blank=True, null=True)
    value_integer = models.BigIntegerField(_('Integer Value'), blank=True, null=True)
    value_decimal = models.DecimalField(_('Decimal Value'), max_digits=15, decimal_places=5, blank=True, null=True)
    value_boolean = models.BooleanField(_('Boolean Value'), blank=True, null=True)
    value_date = models.DateField(_('Date Value'), blank=True, null=True)
    value_datetime = models.DateTimeField(_('DateTime Value'), blank=True, null=True)
    value_file = models.FileField(_('File Value'), upload_to='custom_fields/%Y/%m/%d/', blank=True, null=True)

    class Meta:
        unique_together = (('ticket', 'field'),)
        verbose_name = _('Ticket custom field value')
        verbose_name_plural = _('Ticket custom field values')
        indexes = [
            models.Index(fields=['ticket', 'field']),
        ]

    def __str__(self):
        return f'{self.ticket} / {self.field}'

    def get_value(self):
        """Get the appropriate value based on field data type"""
        data_type = self.field.data_type
        
        if data_type == 'integer':
            return self.value_integer
        elif data_type == 'decimal':
            return self.value_decimal
        elif data_type == 'boolean':
            return self.value_boolean
        elif data_type == 'date':
            return self.value_date
        elif data_type == 'datetime':
            return self.value_datetime
        elif data_type == 'file':
            return self.value_file
        else:
            return self.value or self.value_text

    def set_value(self, value):
        """Set the appropriate value based on field data type"""
        data_type = self.field.data_type
        
        # Clear all typed values first
        self.value_text = None
        self.value_integer = None
        self.value_decimal = None
        self.value_boolean = None
        self.value_date = None
        self.value_datetime = None
        
        # Set the appropriate typed value
        if data_type == 'integer' and value is not None:
            self.value_integer = int(value)
        elif data_type == 'decimal' and value is not None:
            self.value_decimal = Decimal(str(value))
        elif data_type == 'boolean':
            self.value_boolean = bool(value)
        elif data_type == 'date' and value is not None:
            self.value_date = value
        elif data_type == 'datetime' and value is not None:
            self.value_datetime = value
        else:
            self.value_text = str(value) if value is not None else None
        
        # Always set the main value field for backward compatibility
        self.value = str(value) if value is not None else None
