# helpdesk/models/knowledge.py - Knowledge Base Models

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

class KBCategory(models.Model):
    """
    Enhanced knowledge base categories with hierarchy
    """
    # Basic Information
    title = models.CharField(
        _('Title'),
        max_length=100
    )
    slug = models.SlugField(
        _('Slug'),
        unique=True
    )
    description = models.TextField(
        _('Description')
    )

    # Hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subcategories',
        help_text=_('Parent category for hierarchical organization')
    )

    # Settings
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this category is currently visible')
    )
    sort_order = models.PositiveIntegerField(
        _('Sort Order'),
        default=0,
        help_text=_('Order in which categories are displayed')
    )

    # Icon and Color
    icon = models.CharField(
        _('Icon'),
        max_length=50,
        blank=True,
        help_text=_('FontAwesome icon class (e.g., fa-question-circle)')
    )
    color = models.CharField(
        _('Color'),
        max_length=7,
        default='#007bff',
        help_text=_('Hex color code for category identification')
    )

    class Meta:
        ordering = ('sort_order', 'title')
        verbose_name = _('Knowledge base category')
        verbose_name_plural = _('Knowledge base categories')

    def __str__(self):
        if self.parent:
            return f'{self.parent.title} > {self.title}'
        return self.title

    def get_absolute_url(self):
        return reverse('helpdesk:kb_category', kwargs={'slug': self.slug})

    @property
    def item_count(self):
        """Count of items in this category"""
        return self.kbitems.filter(is_published=True).count()

    @property
    def total_item_count(self):
        """Count of items in this category and all subcategories"""
        count = self.item_count
        for subcategory in self.subcategories.all():
            count += subcategory.total_item_count
        return count

class KBItem(models.Model):
    """
    Enhanced knowledge base items with better content management
    """
    # Basic Information
    category = models.ForeignKey(
        KBCategory,
        on_delete=models.CASCADE,
        related_name='kbitems',
        verbose_name=_('Category')
    )
    title = models.CharField(
        _('Title'),
        max_length=100
    )
    slug = models.SlugField(
        _('Slug'),
        blank=True,
        help_text=_('Auto-generated from title if left blank')
    )
    question = models.TextField(
        _('Question')
    )
    answer = models.TextField(
        _('Answer')
    )

    # Content Management
    is_published = models.BooleanField(
        _('Published'),
        default=True,
        help_text=_('Whether this item is visible to users')
    )
    is_featured = models.BooleanField(
        _('Featured'),
        default=False,
        help_text=_('Whether this item appears in featured lists')
    )

    # Ratings and Analytics
    votes = models.IntegerField(
        _('Total Votes'),
        help_text=_('Total number of votes cast for this item'),
        default=0
    )
    recommendations = models.IntegerField(
        _('Positive Votes'),
        help_text=_('Number of votes for this item which were POSITIVE.'),
        default=0
    )
    view_count = models.PositiveIntegerField(
        _('View Count'),
        default=0,
        help_text=_('Number of times this item has been viewed')
    )

    # Tags and Keywords
    tags = models.CharField(
        _('Tags'),
        max_length=500,
        blank=True,
        help_text=_('Comma-separated tags for better searchability')
    )
    keywords = models.CharField(
        _('Keywords'),
        max_length=500,
        blank=True,
        help_text=_('Keywords for search optimization')
    )

    # Authorship
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_kb_items',
        help_text=_('User who created this KB item')
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_kb_items',
        help_text=_('User who last updated this KB item')
    )

    # Timestamps
    created_at = models.DateTimeField(_('Created'), auto_now_add=True)
    last_updated = models.DateTimeField(
        _('Last Updated'),
        help_text=_('The date on which this question was most recently changed.'),
        auto_now=True
    )

    class Meta:
        ordering = ('-is_featured', '-recommendations', 'title')
        verbose_name = _('Knowledge base item')
        verbose_name_plural = _('Knowledge base items')
        indexes = [
            models.Index(fields=['is_published', 'is_featured']),
            models.Index(fields=['category', 'is_published']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def score(self):
        """Calculate score based on votes"""
        if self.votes > 0:
            return round((self.recommendations / self.votes) * 100, 1)
        else:
            return _('Unrated')

    @property
    def tag_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('helpdesk:kb_item', args=(self.id,))

    def vote_up(self):
        """Add a positive vote"""
        self.votes += 1
        self.recommendations += 1
        self.save()

    def vote_down(self):
        """Add a negative vote"""
        self.votes += 1
        self.save()
