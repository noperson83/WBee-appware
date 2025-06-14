# timecard/models.py - Modernized Timecard Models

from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse
from datetime import timedelta, datetime, date, time
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from hr.models import Worker
from project.models import Project

# Shared abstract models
from client.models import TimeStampedModel

class TimesheetPeriod(TimeStampedModel):
    """
    Represents a payroll period for grouping timecards
    """
    PERIOD_TYPES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom Period'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]
    
    name = models.CharField(max_length=100, help_text='Period name (e.g., "Week ending 12/01/2024")')
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default='weekly')
    start_date = models.DateField(help_text='Period start date')
    end_date = models.DateField(help_text='Period end date')
    due_date = models.DateField(null=True, blank=True, help_text='Timesheet submission deadline')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = ['start_date', 'end_date', 'period_type']

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError('End date must be after start date')

    @property
    def total_days(self):
        """Total days in this period"""
        return (self.end_date - self.start_date).days + 1

    @property
    def is_overdue(self):
        """Check if submission deadline has passed"""
        return self.due_date and timezone.now().date() > self.due_date

class TimeCardManager(models.Manager):
    def for_worker_and_period(self, worker, period):
        """Get all timecards for a worker in a specific period"""
        return self.filter(
            worker=worker,
            date__gte=period.start_date,
            date__lte=period.end_date
        )

    def for_project_and_period(self, project, period):
        """Get all timecards for a project in a specific period"""
        return self.filter(
            project=project,
            date__gte=period.start_date,
            date__lte=period.end_date
        )

    def weekly_summary(self, worker, week_start):
        """Get weekly summary for a worker"""
        week_end = week_start + timedelta(days=6)
        return self.filter(
            worker=worker,
            date__gte=week_start,
            date__lte=week_end
        )

class TimeCard(TimeStampedModel):
    """
    Modernized timecard model with better validation and calculations
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    WORK_TYPE_CHOICES = [
        ('regular', 'Regular Time'),
        ('overtime', 'Overtime'),
        ('double_time', 'Double Time'),
        ('holiday', 'Holiday'),
        ('sick', 'Sick Leave'),
        ('vacation', 'Vacation'),
        ('personal', 'Personal Time'),
        ('training', 'Training'),
        ('travel', 'Travel Time'),
        ('on_call', 'On Call'),
    ]

    # Basic Information
    date = models.DateField(help_text='Work date')
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="timecards",
        help_text='Worker who worked these hours'
    )
    project = models.ForeignKey(
        Project, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text='Project worked on'
    )
    
    # Time Tracking
    start_time = models.TimeField(help_text='Start time')
    end_time = models.TimeField(help_text='End time')
    lunch_start = models.TimeField(null=True, blank=True, help_text='Lunch break start')
    lunch_end = models.TimeField(null=True, blank=True, help_text='Lunch break end')
    
    # Break tracking
    break_minutes = models.PositiveIntegerField(
        default=0, 
        validators=[MaxValueValidator(480)],  # Max 8 hours of breaks
        help_text='Additional break time in minutes'
    )
    
    # Work Details
    work_type = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES, default='regular')
    description = models.TextField(blank=True, help_text='Description of work performed')
    location = models.CharField(max_length=200, blank=True, help_text='Work location')
    
    # Rates and Calculations
    hourly_rate = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Hourly rate for this timecard (overrides worker default)'
    )
    
    # Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_timecards'
    )
    
    # Additional Information
    mileage = models.DecimalField(
        max_digits=6, 
        decimal_places=1, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.0'))],
        help_text='Miles driven for work'
    )
    expenses = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Work-related expenses'
    )
    
    # Period tracking
    timesheet_period = models.ForeignKey(
        TimesheetPeriod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Payroll period this timecard belongs to'
    )
    
    # Notes and attachments
    notes = models.TextField(blank=True, help_text='Additional notes')
    photo = models.ImageField(
        upload_to='timecards/photos/%Y/%m/%d/', 
        null=True, 
        blank=True,
        help_text='Photo from work site'
    )
    
    objects = TimeCardManager()

    class Meta:
        ordering = ['-date', '-start_time']
        unique_together = ['worker', 'date', 'start_time', 'project']
        indexes = [
            models.Index(fields=['worker', 'date']),
            models.Index(fields=['project', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.worker} - {self.date} ({self.total_hours:.2f}h)"

    def clean(self):
        """Validate timecard data"""
        errors = {}
        
        # Validate time logic
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                errors['end_time'] = 'End time must be after start time'
        
        # Validate lunch break
        if self.lunch_start and self.lunch_end:
            if self.lunch_start >= self.lunch_end:
                errors['lunch_end'] = 'Lunch end time must be after lunch start time'
            
            # Check if lunch is within work hours
            if self.start_time and self.end_time:
                if not (self.start_time <= self.lunch_start < self.end_time):
                    errors['lunch_start'] = 'Lunch start must be within work hours'
                if not (self.start_time < self.lunch_end <= self.end_time):
                    errors['lunch_end'] = 'Lunch end must be within work hours'
        
        # Validate lunch start/end together
        if bool(self.lunch_start) != bool(self.lunch_end):
            if not self.lunch_start:
                errors['lunch_start'] = 'Lunch start time required when lunch end is specified'
            else:
                errors['lunch_end'] = 'Lunch end time required when lunch start is specified'
        
        # Validate date is not in the future
        if self.date and self.date > timezone.now().date():
            errors['date'] = 'Cannot create timecard for future dates'
        
        # Check for overlapping timecards
        if self.date and self.start_time and self.end_time:
            overlapping = TimeCard.objects.filter(
                worker=self.worker,
                date=self.date,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            ).exclude(pk=self.pk)
            
            if overlapping.exists():
                errors['start_time'] = 'This timecard overlaps with an existing timecard'
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Auto-assign to current period if not set
        if not self.timesheet_period:
            period = TimesheetPeriod.objects.filter(
                start_date__lte=self.date,
                end_date__gte=self.date,
                is_active=True
            ).first()
            if period:
                self.timesheet_period = period
        
        # Set submitted timestamp
        if self.status == 'submitted' and not self.submitted_at:
            self.submitted_at = timezone.now()
        
        # Set approved timestamp
        if self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()
        
        super().save(*args, **kwargs)

    @property
    def total_hours(self):
        """Calculate total hours worked"""
        if not (self.start_time and self.end_time):
            return Decimal('0.00')
        
        # Calculate work time
        work_start = datetime.combine(date.today(), self.start_time)
        work_end = datetime.combine(date.today(), self.end_time)
        
        # Handle overnight shifts
        if work_end <= work_start:
            work_end += timedelta(days=1)
        
        total_time = work_end - work_start
        
        # Subtract lunch break
        if self.lunch_start and self.lunch_end:
            lunch_start = datetime.combine(date.today(), self.lunch_start)
            lunch_end = datetime.combine(date.today(), self.lunch_end)
            
            if lunch_end <= lunch_start:
                lunch_end += timedelta(days=1)
            
            lunch_duration = lunch_end - lunch_start
            total_time -= lunch_duration
        
        # Subtract additional breaks
        total_time -= timedelta(minutes=self.break_minutes)
        
        # Convert to decimal hours
        total_seconds = total_time.total_seconds()
        return Decimal(str(round(total_seconds / 3600, 2)))

    @property
    def regular_hours(self):
        """Calculate regular hours (up to 8 per day)"""
        total = self.total_hours
        if self.work_type in ['sick', 'vacation', 'personal']:
            return total  # PTO hours count as regular
        return min(total, Decimal('8.00'))

    @property
    def overtime_hours(self):
        """Calculate overtime hours (over 8 per day)"""
        if self.work_type in ['sick', 'vacation', 'personal']:
            return Decimal('0.00')  # No OT for PTO
        total = self.total_hours
        return max(total - Decimal('8.00'), Decimal('0.00'))

    @property
    def effective_hourly_rate(self):
        """Get the effective hourly rate for this timecard"""
        if self.hourly_rate:
            return self.hourly_rate
        elif hasattr(self.worker, 'hourly') and self.worker.hourly:
            return Decimal(str(self.worker.hourly))
        elif hasattr(self.worker, 'salary') and self.worker.salary:
            # Convert annual salary to hourly (2080 hours per year)
            return Decimal(str(self.worker.salary)) / Decimal('2080')
        return Decimal('0.00')

    @property
    def total_pay(self):
        """Calculate total pay for this timecard"""
        rate = self.effective_hourly_rate
        regular_pay = self.regular_hours * rate
        overtime_pay = self.overtime_hours * rate * Decimal('1.5')  # 1.5x for OT
        return regular_pay + overtime_pay

    @property
    def lunch_duration_minutes(self):
        """Calculate lunch break duration in minutes"""
        if not (self.lunch_start and self.lunch_end):
            return 0
        
        lunch_start = datetime.combine(date.today(), self.lunch_start)
        lunch_end = datetime.combine(date.today(), self.lunch_end)
        
        if lunch_end <= lunch_start:
            lunch_end += timedelta(days=1)
        
        duration = lunch_end - lunch_start
        return int(duration.total_seconds() / 60)

    def get_absolute_url(self):
        """Returns the url to access this timecard"""
        return reverse('timecard-detail', args=[str(self.id)])

    def can_edit(self):
        """Check if timecard can be edited"""
        return self.status in ['draft', 'rejected']

    def can_submit(self):
        """Check if timecard can be submitted"""
        return self.status == 'draft' and self.total_hours > 0

    def can_approve(self):
        """Check if timecard can be approved"""
        return self.status == 'submitted'

class TimeCardAttachment(models.Model):
    """
    File attachments for timecards (receipts, photos, etc.)
    """
    timecard = models.ForeignKey(
        TimeCard,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='timecards/attachments/%Y/%m/%d/',
        help_text='Attachment file'
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text='Description of the attachment'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timecard} - {self.description or 'Attachment'}"

class TimesheetSummary(TimeStampedModel):
    """
    Weekly/period summary for worker timesheets
    """
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='timesheet_summaries'
    )
    period = models.ForeignKey(
        TimesheetPeriod,
        on_delete=models.CASCADE,
        related_name='summaries'
    )
    
    # Calculated totals
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    regular_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    sick_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    vacation_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Financial totals
    total_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_mileage = models.DecimalField(max_digits=8, decimal_places=1, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    is_complete = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['worker', 'period']
        ordering = ['-period__start_date']

    def __str__(self):
        return f"{self.worker} - {self.period}"

    def calculate_totals(self):
        """Recalculate all totals from timecards"""
        timecards = TimeCard.objects.filter(
            worker=self.worker,
            date__gte=self.period.start_date,
            date__lte=self.period.end_date
        )
        
        self.total_hours = sum(tc.total_hours for tc in timecards)
        self.regular_hours = sum(tc.regular_hours for tc in timecards)
        self.overtime_hours = sum(tc.overtime_hours for tc in timecards)
        
        # Calculate by work type
        self.sick_hours = sum(
            tc.total_hours for tc in timecards 
            if tc.work_type == 'sick'
        )
        self.vacation_hours = sum(
            tc.total_hours for tc in timecards 
            if tc.work_type == 'vacation'
        )
        
        # Financial totals
        self.total_pay = sum(tc.total_pay for tc in timecards)
        self.total_mileage = sum(
            tc.mileage for tc in timecards 
            if tc.mileage
        ) or Decimal('0.0')
        self.total_expenses = sum(
            tc.expenses for tc in timecards 
            if tc.expenses
        ) or Decimal('0.00')
        
        self.save()

    @property
    def expected_hours(self):
        """Expected hours for this period (typically 40 for full-time)"""
        # This could be configurable per worker
        return Decimal('40.00')

    @property
    def variance_hours(self):
        """Difference between expected and actual hours"""
        return self.total_hours - self.expected_hours
