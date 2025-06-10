# todo/models.py - Modernized Todo/Task Management Models

from django.db import models
from django.contrib.auth.models import Group
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django_extensions.db.fields import AutoSlugField
from decimal import Decimal
from datetime import date, datetime, timedelta

# Shared abstract base models
from client.models import TimeStampedModel
from hr.models import JobPosition, Worker
from project.models import ScopeOfWork, Project

class TaskListManager(models.Manager):
    def for_group(self, group):
        """Get task lists for a specific group"""
        return self.filter(group=group, is_active=True)

    def by_priority(self):
        """Get task lists ordered by priority"""
        return self.filter(is_active=True).order_by('priority', 'name')

    def with_pending_tasks(self):
        """Get task lists that have incomplete tasks"""
        return self.filter(
            tasks__completed=False,
            is_active=True
        ).distinct()

class TaskList(TimeStampedModel):
    """
    Modernized task list with enhanced categorization and workflow
    """
    LIST_TYPES = [
        ('project', 'Project Tasks'),
        ('maintenance', 'Maintenance'),
        ('training', 'Training'),
        ('daily', 'Daily Operations'),
        ('backlog', 'Backlog'),
        ('template', 'Task Template'),
        ('personal', 'Personal Tasks'),
        ('custom', 'Custom List'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    # Basic Information
    name = models.CharField(max_length=200, help_text='Task list name')
    slug = AutoSlugField(
        populate_from=['name', 'scope', 'group', 'id'], 
        blank=True, 
        null=True,
        help_text='Auto-generated URL slug'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of this task list'
    )
    list_type = models.CharField(
        max_length=20,
        choices=LIST_TYPES,
        default='custom',
        help_text='Type of task list'
    )

    # Organization
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        null=True,
        help_text='Group that owns this task list'
    )
    scope = models.ForeignKey(
        "project.ScopeOfWork", 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name="task_lists",
        help_text='Associated scope of work'
    )
    project = models.ForeignKey(
        "project.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="task_lists",
        help_text='Associated project'
    )

    # Priority and Status
    priority = models.PositiveIntegerField(
        default=9999, 
        validators=[MinValueValidator(1), MaxValueValidator(99999)],
        help_text='Priority (lower numbers = higher priority)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text='Current status of the task list'
    )

    # Settings
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this task list is currently active'
    )
    is_template = models.BooleanField(
        default=False,
        help_text='Use this list as a template for creating new lists'
    )
    auto_assign = models.BooleanField(
        default=False,
        help_text='Automatically assign new tasks to group members'
    )

    # Workflow settings
    requires_approval = models.BooleanField(
        default=False,
        help_text='Tasks require approval before completion'
    )
    send_notifications = models.BooleanField(
        default=True,
        help_text='Send notifications for task updates'
    )

    # Dates
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text='When work on this list should begin'
    )
    target_completion_date = models.DateField(
        null=True,
        blank=True,
        help_text='Target completion date for all tasks'
    )
    completed_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when all tasks were completed'
    )

    # Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_task_lists',
        help_text='User who created this task list'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_task_lists',
        help_text='Current owner/manager of this task list'
    )

    objects = TaskListManager()

    class Meta:
        ordering = ["priority", "name"]
        verbose_name_plural = "Task Lists"
        unique_together = ("group", "slug")
        indexes = [
            models.Index(fields=['group', 'is_active']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['project', 'scope']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Validate task list data"""
        if self.start_date and self.target_completion_date:
            if self.start_date > self.target_completion_date:
                raise ValidationError('Target completion date must be after start date')

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Auto-complete if all tasks are done
        if self.status == 'active' and self.all_tasks_completed:
            self.status = 'completed'
            if not self.completed_date:
                self.completed_date = timezone.now().date()
        
        super().save(*args, **kwargs)

    @property
    def task_count(self):
        """Total number of tasks"""
        return self.tasks.count()

    @property
    def completed_task_count(self):
        """Number of completed tasks"""
        return self.tasks.filter(completed=True).count()

    @property
    def pending_task_count(self):
        """Number of pending tasks"""
        return self.tasks.filter(completed=False).count()

    @property
    def completion_percentage(self):
        """Percentage of tasks completed"""
        if self.task_count == 0:
            return 0
        return round((self.completed_task_count / self.task_count) * 100, 1)

    @property
    def all_tasks_completed(self):
        """Check if all tasks are completed"""
        return self.task_count > 0 and self.pending_task_count == 0

    @property
    def total_estimated_hours(self):
        """Total estimated hours for all tasks"""
        return self.tasks.aggregate(
            total=models.Sum('total_hours')
        )['total'] or Decimal('0.00')

    @property
    def is_overdue(self):
        """Check if task list is overdue"""
        if not self.target_completion_date:
            return False
        return (
            self.target_completion_date < timezone.now().date() and 
            not self.all_tasks_completed
        )

    @property
    def days_until_due(self):
        """Days until target completion date"""
        if not self.target_completion_date:
            return None
        delta = self.target_completion_date - timezone.now().date()
        return delta.days

    def get_absolute_url(self):
        return reverse('todo:task_list_detail', kwargs={'slug': self.slug})

    def clone_as_template(self, new_name=None):
        """Create a copy of this task list as a template"""
        new_name = new_name or f"{self.name} (Template)"
        
        # Clone the task list
        new_list = TaskList.objects.create(
            name=new_name,
            description=self.description,
            list_type='template',
            group=self.group,
            is_template=True,
            created_by=self.created_by
        )
        
        # Clone all tasks
        for task in self.tasks.all():
            task.clone_to_list(new_list, reset_dates=True)
        
        return new_list

class TaskManager(models.Manager):
    def pending(self):
        """Get incomplete tasks"""
        return self.filter(completed=False)

    def completed(self):
        """Get completed tasks"""
        return self.filter(completed=True)

    def overdue(self):
        """Get overdue tasks"""
        return self.filter(
            due_date__lt=timezone.now().date(),
            completed=False
        )

    def due_soon(self, days=7):
        """Get tasks due within X days"""
        cutoff = timezone.now().date() + timedelta(days=days)
        return self.filter(
            due_date__lte=cutoff,
            due_date__gte=timezone.now().date(),
            completed=False
        )

    def assigned_to(self, user):
        """Get tasks assigned to a user"""
        return self.filter(assigned_to=user)

    def for_group(self, group):
        """Get tasks for a specific group"""
        return self.filter(task_list__group=group)

class Task(TimeStampedModel):
    """
    Modernized task model with enhanced tracking and workflow
    """
    PRIORITY_CHOICES = [
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Normal'),
        (4, 'Low'),
        (5, 'Backlog'),
    ]

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('blocked', 'Blocked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ]

    # Basic Information
    title = models.CharField(
        max_length=200,
        help_text='Brief task description'
    )
    description = models.TextField(
        blank=True,
        help_text='Detailed task description'
    )
    task_list = models.ForeignKey(
        TaskList, 
        on_delete=models.CASCADE, 
        related_name='tasks',
        help_text='Task list this task belongs to'
    )

    # Work Estimation
    allotted_time = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.25'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Estimated hours to complete this task'
    )
    team_size = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text='Number of people required'
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        help_text='Task difficulty level'
    )

    # Assignment and Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name="created_tasks", 
        on_delete=models.CASCADE,
        help_text='User who created this task'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="assigned_tasks",
        on_delete=models.SET_NULL,
        help_text='User assigned to complete this task'
    )
    position = models.ForeignKey(
        JobPosition, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name="required_for_tasks", 
        help_text='Position/role required for this task'
    )

    # Status and Priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo',
        help_text='Current task status'
    )
    priority = models.PositiveIntegerField(
        choices=PRIORITY_CHOICES,
        default=3,
        help_text='Task priority level'
    )

    # Dates and Timing
    created_date = models.DateTimeField(
        default=timezone.now,
        help_text='When this task was created'
    )
    due_date = models.DateField(
        blank=True, 
        null=True,
        help_text='When this task should be completed'
    )
    start_date = models.DateField(
        blank=True,
        null=True,
        help_text='When work on this task should begin'
    )
    completed_date = models.DateTimeField(
        blank=True, 
        null=True,
        help_text='When this task was completed'
    )

    # Completion tracking
    completed = models.BooleanField(
        default=False,
        help_text='Whether this task is completed'
    )
    completion_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        help_text='Percentage of task completed (0-100)'
    )

    # Additional Information
    note = models.TextField(
        blank=True, 
        null=True,
        help_text='Additional notes or instructions'
    )
    blockers = models.TextField(
        blank=True,
        help_text='What is blocking this task from completion'
    )

    # Dependencies
    depends_on = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='blocks',
        help_text='Tasks that must be completed before this one'
    )

    # Approval workflow
    requires_approval = models.BooleanField(
        default=False,
        help_text='Task completion requires approval'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name='approved_tasks',
        on_delete=models.SET_NULL,
        help_text='User who approved task completion'
    )
    approved_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text='When task completion was approved'
    )

    # Time tracking
    actual_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Actual hours spent on this task'
    )

    objects = TaskManager()

    class Meta:
        ordering = ["priority", "due_date", "created_date"]
        indexes = [
            models.Index(fields=['assigned_to', 'completed']),
            models.Index(fields=['due_date', 'completed']),
            models.Index(fields=['task_list', 'status']),
            models.Index(fields=['priority', 'due_date']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        """Validate task data"""
        errors = {}
        
        if self.start_date and self.due_date:
            if self.start_date > self.due_date:
                errors['due_date'] = 'Due date must be after start date'
        
        if self.completion_percentage > 0 and self.status == 'todo':
            errors['status'] = 'Status should not be "To Do" if progress has been made'
        
        if self.completed and self.completion_percentage < 100:
            errors['completion_percentage'] = 'Completion percentage should be 100% if task is marked complete'
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Auto-set completion date
        if self.completed and not self.completed_date:
            self.completed_date = timezone.now()
        elif not self.completed:
            self.completed_date = None
        
        # Auto-set status based on completion
        if self.completed and self.status not in ['completed', 'cancelled']:
            self.status = 'completed'
            self.completion_percentage = 100
        elif not self.completed and self.status == 'completed':
            self.status = 'todo'
        
        # Update task list status
        old_completed = None
        if self.pk:
            old_completed = Task.objects.get(pk=self.pk).completed
        
        super().save(*args, **kwargs)
        
        # Update task list completion if this task's status changed
        if old_completed != self.completed:
            self.task_list.save()

    @property
    def total_hours(self):
        """Calculate total estimated hours (time × team size)"""
        return self.allotted_time * self.team_size

    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if not self.due_date or self.completed:
            return False
        return self.due_date < timezone.now().date()

    @property
    def days_until_due(self):
        """Days until due date"""
        if not self.due_date:
            return None
        delta = self.due_date - timezone.now().date()
        return delta.days

    @property
    def can_start(self):
        """Check if all dependencies are completed"""
        return not self.depends_on.filter(completed=False).exists()

    @property
    def estimated_cost(self):
        """Calculate estimated cost based on position rate"""
        if not self.position:
            return Decimal('0.00')
        
        rate = Decimal('0.00')
        if self.position.hors and self.position.hourly:
            rate = self.position.hourly
        elif not self.position.hors and self.position.salary:
            # Convert annual salary to hourly (2080 hours/year)
            rate = self.position.salary / Decimal('2080')
        
        return self.total_hours * rate

    @property
    def actual_cost(self):
        """Calculate actual cost based on hours worked"""
        if not (self.actual_hours and self.position):
            return Decimal('0.00')
        
        rate = Decimal('0.00')
        if self.position.hors and self.position.hourly:
            rate = self.position.hourly
        elif not self.position.hors and self.position.salary:
            rate = self.position.salary / Decimal('2080')
        
        return self.actual_hours * rate * self.team_size

    @property
    def cost_variance(self):
        """Calculate cost variance (actual - estimated)"""
        if self.actual_hours and self.position:
            return self.actual_cost - self.estimated_cost
        return None

    @property
    def time_variance(self):
        """Calculate time variance (actual - estimated)"""
        if self.actual_hours:
            return self.actual_hours - self.total_hours
        return None

    def get_absolute_url(self):
        return reverse("todo:task_detail", kwargs={"task_id": self.id})

    def mark_completed(self, completed_by=None, notes=''):
        """Mark task as completed"""
        self.completed = True
        self.status = 'completed'
        self.completion_percentage = 100
        self.completed_date = timezone.now()
        
        if notes:
            self.note = f"{self.note}\n\nCompleted: {notes}".strip()
        
        self.save()

    def clone_to_list(self, target_list, reset_dates=False):
        """Clone this task to another task list"""
        new_task = Task.objects.create(
            title=self.title,
            description=self.description,
            task_list=target_list,
            allotted_time=self.allotted_time,
            team_size=self.team_size,
            difficulty=self.difficulty,
            position=self.position,
            priority=self.priority,
            note=self.note,
            created_by=self.created_by,
            requires_approval=self.requires_approval,
            due_date=None if reset_dates else self.due_date,
            start_date=None if reset_dates else self.start_date
        )
        
        # Clone dependencies (if they exist in target list)
        for dependency in self.depends_on.all():
            try:
                target_dependency = target_list.tasks.get(title=dependency.title)
                new_task.depends_on.add(target_dependency)
            except Task.DoesNotExist:
                pass  # Skip dependencies that don't exist in target list
        
        return new_task

class Comment(TimeStampedModel):
    """
    Enhanced comment model with better tracking and features
    """
    COMMENT_TYPES = [
        ('note', 'General Note'),
        ('update', 'Status Update'),
        ('question', 'Question'),
        ('blocker', 'Blocker Reported'),
        ('approval', 'Approval Comment'),
        ('review', 'Review Comment'),
    ]

    # Basic Information
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        help_text='User who wrote this comment'
    )
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE,
        related_name='comments',
        help_text='Task this comment relates to'
    )
    body = models.TextField(
        help_text='Comment content'
    )
    comment_type = models.CharField(
        max_length=20,
        choices=COMMENT_TYPES,
        default='note',
        help_text='Type of comment'
    )

    # Metadata
    date = models.DateTimeField(
        default=timezone.now,
        help_text='When this comment was posted'
    )
    
    # Features
    is_private = models.BooleanField(
        default=False,
        help_text='Only visible to task assignee and creator'
    )
    requires_response = models.BooleanField(
        default=False,
        help_text='This comment requires a response'
    )
    
    # File attachment
    attachment = models.FileField(
        upload_to='task_comments/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Optional file attachment'
    )

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['task', 'date']),
            models.Index(fields=['author', 'date']),
        ]

    def __str__(self):
        return self.snippet()

    def snippet(self, length=50):
        """Return a short snippet of the comment"""
        return f"{self.author.get_short_name()}: {self.body[:length]}{'...' if len(self.body) > length else ''}"

    @property
    def is_recent(self):
        """Check if comment was posted recently (within 24 hours)"""
        return (timezone.now() - self.date).total_seconds() < 86400  # 24 hours

class TaskAttachment(models.Model):
    """
    File attachments for tasks
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='task_attachments/%Y/%m/%d/',
        help_text='Task-related file'
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text='Description of the attachment'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text='User who uploaded this file'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.task.title} - {self.description or 'Attachment'}"

class TaskTemplate(TimeStampedModel):
    """
    Reusable task templates for common workflows
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('project', 'Project Tasks'),
            ('maintenance', 'Maintenance'),
            ('onboarding', 'Employee Onboarding'),
            ('training', 'Training'),
            ('inspection', 'Inspection'),
            ('custom', 'Custom'),
        ],
        default='custom'
    )
    
    # Template settings
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

    def create_tasks_for_list(self, task_list, assigned_to=None):
        """Create tasks from this template in the specified task list"""
        template_tasks = self.template_tasks.all()
        created_tasks = []
        
        for template_task in template_tasks:
            task = Task.objects.create(
                title=template_task.title,
                description=template_task.description,
                task_list=task_list,
                allotted_time=template_task.allotted_time,
                team_size=template_task.team_size,
                difficulty=template_task.difficulty,
                priority=template_task.priority,
                position=template_task.position,
                created_by=task_list.created_by or self.created_by,
                assigned_to=assigned_to
            )
            created_tasks.append(task)
        
        return created_tasks

class TaskTemplateItem(models.Model):
    """
    Individual task items within a template
    """
    template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name='template_tasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    allotted_time = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.25')
    )
    team_size = models.PositiveIntegerField(default=1)
    difficulty = models.CharField(
        max_length=10,
        choices=Task.DIFFICULTY_CHOICES,
        default='medium'
    )
    priority = models.PositiveIntegerField(
        choices=Task.PRIORITY_CHOICES,
        default=3
    )
    position = models.ForeignKey(
        JobPosition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'priority']

    def __str__(self):
        return f"{self.template.name} - {self.title}"

# Default data creation functions
def create_default_task_templates():
    """Create default task templates for different business workflows"""
    
    from django.contrib.auth.models import Group
    from hr.models import JobPosition
    
    try:
        # Create default groups if they don't exist
        project_group, _ = Group.objects.get_or_create(name='Project Management')
        maintenance_group, _ = Group.objects.get_or_create(name='Maintenance Team')
        training_group, _ = Group.objects.get_or_create(name='Training Department')
        admin_group, _ = Group.objects.get_or_create(name='Administration')
        
        # Get some positions (create basic ones if needed)
        try:
            project_manager = JobPosition.objects.get(name__icontains='Project Manager')
        except JobPosition.DoesNotExist:
            project_manager = JobPosition.objects.create(
                name='Project Manager',
                hors=False,
                salary=Decimal('75000.00')
            )
        
        try:
            technician = JobPosition.objects.get(name__icontains='Technician')
        except JobPosition.DoesNotExist:
            technician = JobPosition.objects.create(
                name='Field Technician',
                hors=True,
                hourly=Decimal('25.00')
            )
        
        try:
            admin_user = Worker.objects.filter(is_staff=True).first()
            if not admin_user:
                admin_user = Worker.objects.create(
                    email='admin@company.com',
                    first_name='System',
                    last_name='Administrator',
                    is_staff=True
                )
        except:
            admin_user = None
        
        # Project Management Templates
        project_templates = [
            {
                'name': 'New Project Setup',
                'description': 'Standard tasks for initiating a new project',
                'category': 'project',
                'tasks': [
                    ('Project Kickoff Meeting', 'Schedule and conduct initial project meeting', 2.0, 1, 'medium', 1),
                    ('Define Project Scope', 'Document project requirements and deliverables', 4.0, 1, 'hard', 1),
                    ('Create Project Timeline', 'Develop detailed project schedule', 3.0, 1, 'medium', 2),
                    ('Assign Team Members', 'Identify and assign project team roles', 1.0, 1, 'easy', 2),
                    ('Set Up Project Tracking', 'Configure project management tools', 1.5, 1, 'medium', 3),
                ]
            },
            {
                'name': 'Project Closeout',
                'description': 'Tasks for properly closing out completed projects',
                'category': 'project',
                'tasks': [
                    ('Final Client Walkthrough', 'Conduct final inspection with client', 2.0, 2, 'medium', 1),
                    ('Documentation Handover', 'Provide all project documentation to client', 1.0, 1, 'easy', 1),
                    ('Equipment Inventory', 'Account for all project equipment and materials', 1.5, 1, 'easy', 2),
                    ('Project Review Meeting', 'Conduct lessons learned session with team', 1.5, 1, 'medium', 3),
                    ('Close Financial Records', 'Finalize all project billing and costs', 2.0, 1, 'medium', 2),
                ]
            }
        ]
        
        # Maintenance Templates
        maintenance_templates = [
            {
                'name': 'Monthly Equipment Maintenance',
                'description': 'Regular monthly maintenance tasks for equipment',
                'category': 'maintenance',
                'tasks': [
                    ('Visual Equipment Inspection', 'Check all equipment for visible damage', 1.0, 1, 'easy', 2),
                    ('Clean Equipment', 'Perform routine cleaning of all equipment', 2.0, 1, 'easy', 3),
                    ('Test Functionality', 'Run operational tests on critical equipment', 1.5, 1, 'medium', 1),
                    ('Update Maintenance Log', 'Document all maintenance activities', 0.5, 1, 'easy', 4),
                    ('Order Replacement Parts', 'Identify and order any needed replacement parts', 1.0, 1, 'medium', 2),
                ]
            },
            {
                'name': 'Emergency Response Checklist',
                'description': 'Critical tasks for emergency situations',
                'category': 'maintenance',
                'tasks': [
                    ('Assess Safety', 'Ensure area is safe for personnel', 0.25, 1, 'critical', 1),
                    ('Notify Management', 'Contact appropriate supervisors immediately', 0.25, 1, 'critical', 1),
                    ('Document Incident', 'Record details of the emergency', 0.5, 1, 'medium', 2),
                    ('Implement Temporary Fix', 'Apply temporary solution if safe to do so', 1.0, 2, 'hard', 2),
                    ('Schedule Permanent Repair', 'Arrange for proper repair or replacement', 0.5, 1, 'medium', 3),
                ]
            }
        ]
        
        # Training Templates
        training_templates = [
            {
                'name': 'New Employee Onboarding',
                'description': 'Complete onboarding checklist for new hires',
                'category': 'onboarding',
                'tasks': [
                    ('Welcome & Orientation', 'Provide company overview and welcome', 2.0, 1, 'easy', 1),
                    ('IT Setup', 'Set up computer, email, and system access', 1.5, 1, 'medium', 1),
                    ('Safety Training', 'Complete required safety training modules', 4.0, 1, 'medium', 2),
                    ('Department Introduction', 'Meet team members and learn department processes', 2.0, 1, 'easy', 2),
                    ('First Week Check-in', 'Schedule follow-up meeting with supervisor', 0.5, 1, 'easy', 3),
                ]
            },
            {
                'name': 'Equipment Certification Training',
                'description': 'Training program for equipment operation certification',
                'category': 'training',
                'tasks': [
                    ('Theory Training', 'Complete classroom portion of training', 8.0, 1, 'medium', 1),
                    ('Hands-on Practice', 'Practice equipment operation under supervision', 16.0, 1, 'hard', 2),
                    ('Written Exam', 'Pass written examination', 1.0, 1, 'medium', 3),
                    ('Practical Assessment', 'Demonstrate competency in equipment operation', 2.0, 1, 'hard', 3),
                    ('Certification Documentation', 'Complete and file certification paperwork', 0.5, 1, 'easy', 4),
                ]
            }
        ]
        
        # Inspection Templates
        inspection_templates = [
            {
                'name': 'Site Safety Inspection',
                'description': 'Weekly safety inspection checklist',
                'category': 'inspection',
                'tasks': [
                    ('PPE Compliance Check', 'Verify all personnel using proper PPE', 0.5, 1, 'medium', 1),
                    ('Hazard Identification', 'Identify and document any safety hazards', 1.0, 1, 'medium', 1),
                    ('Equipment Safety Check', 'Inspect equipment for safety compliance', 1.5, 1, 'medium', 2),
                    ('Emergency Equipment Check', 'Verify emergency equipment is accessible', 0.5, 1, 'easy', 2),
                    ('Document Findings', 'Complete inspection report and file', 0.5, 1, 'easy', 3),
                ]
            }
        ]
        
        # Create all templates
        all_templates = (
            project_templates + maintenance_templates + 
            training_templates + inspection_templates
        )
        
        for template_data in all_templates:
            # Create the template
            template, created = TaskTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'description': template_data['description'],
                    'category': template_data['category'],
                    'created_by': admin_user
                }
            )
            
            if created:
                # Create template tasks
                for order, (title, description, hours, team_size, difficulty, priority) in enumerate(template_data['tasks']):
                    # Convert difficulty to priority number if it's 'critical'
                    if difficulty == 'critical':
                        priority_num = 1
                        difficulty = 'hard'
                    else:
                        priority_num = priority
                    
                    TaskTemplateItem.objects.create(
                        template=template,
                        title=title,
                        description=description,
                        allotted_time=Decimal(str(hours)),
                        team_size=team_size,
                        difficulty=difficulty,
                        priority=priority_num,
                        position=project_manager if template_data['category'] == 'project' else technician,
                        order=order + 1
                    )
        
        print("Default task templates created successfully!")
        
    except Exception as e:
        print(f"Error creating default task templates: {str(e)}")

def create_default_task_lists():
    """Create default task lists for common workflows"""
    
    from django.contrib.auth.models import Group
    
    try:
        # Get or create groups
        groups = {}
        group_names = ['Project Management', 'Maintenance Team', 'Training Department', 'Administration']
        
        for group_name in group_names:
            groups[group_name], _ = Group.objects.get_or_create(name=group_name)
        
        try:
            admin_user = Worker.objects.filter(is_staff=True).first()
        except:
            admin_user = None
        
        # Default task lists
        default_lists = [
            {
                'name': 'Daily Operations Checklist',
                'description': 'Daily tasks for smooth operations',
                'list_type': 'daily',
                'group': groups['Administration'],
                'priority': 1,
                'tasks': [
                    ('Check Email and Messages', 'Review and respond to important communications', 0.5, 1, 'easy', 3),
                    ('Review Daily Schedule', 'Confirm appointments and meetings for the day', 0.25, 1, 'easy', 2),
                    ('Equipment Status Check', 'Verify all critical equipment is operational', 0.5, 1, 'medium', 2),
                    ('Update Project Status', 'Update progress on active projects', 1.0, 1, 'medium', 3),
                ]
            },
            {
                'name': 'Weekly Team Meeting Prep',
                'description': 'Preparation tasks for weekly team meetings',
                'list_type': 'project',
                'group': groups['Project Management'],
                'priority': 2,
                'tasks': [
                    ('Gather Project Updates', 'Collect status updates from all active projects', 1.0, 1, 'medium', 2),
                    ('Review Metrics Dashboard', 'Check KPIs and performance metrics', 0.5, 1, 'medium', 3),
                    ('Prepare Meeting Agenda', 'Create agenda for upcoming team meeting', 0.5, 1, 'easy', 3),
                    ('Schedule Follow-up Actions', 'Plan follow-up tasks from previous meetings', 0.5, 1, 'medium', 4),
                ]
            },
            {
                'name': 'Equipment Maintenance Backlog',
                'description': 'Ongoing maintenance tasks that need attention',
                'list_type': 'backlog',
                'group': groups['Maintenance Team'],
                'priority': 5,
                'tasks': [
                    ('Calibrate Test Equipment', 'Annual calibration of precision instruments', 4.0, 1, 'hard', 2),
                    ('Update Equipment Documentation', 'Review and update equipment manuals', 2.0, 1, 'medium', 4),
                    ('Inventory Spare Parts', 'Count and organize spare parts inventory', 3.0, 1, 'medium', 3),
                    ('Schedule Deep Cleaning', 'Plan thorough cleaning of equipment storage', 1.0, 1, 'easy', 4),
                ]
            }
        ]
        
        # Create task lists
        for list_data in default_lists:
            task_list, created = TaskList.objects.get_or_create(
                name=list_data['name'],
                group=list_data['group'],
                defaults={
                    'description': list_data['description'],
                    'list_type': list_data['list_type'],
                    'priority': list_data['priority'],
                    'created_by': admin_user,
                    'owner': admin_user
                }
            )
            
            if created:
                # Create tasks for this list
                for title, description, hours, team_size, difficulty, priority in list_data['tasks']:
                    Task.objects.create(
                        title=title,
                        description=description,
                        task_list=task_list,
                        allotted_time=Decimal(str(hours)),
                        team_size=team_size,
                        difficulty=difficulty,
                        priority=priority,
                        created_by=admin_user
                    )
        
        print("Default task lists created successfully!")
        
    except Exception as e:
        print(f"Error creating default task lists: {str(e)}")

def create_sample_project_tasks():
    """Create sample tasks for project management demonstration"""
    
    try:
        from project.models import Project
        
        # Get a sample project (or create one for demo)
        try:
            sample_project = Project.objects.first()
            if not sample_project:
                print("No projects found. Create a project first to add sample tasks.")
                return
        except:
            print("Project model not available. Skipping project task creation.")
            return
        
        try:
            admin_user = Worker.objects.filter(is_staff=True).first()
        except:
            admin_user = None
        
        # Create project-specific task list
        project_list, created = TaskList.objects.get_or_create(
            name=f'{sample_project.name} - Implementation Tasks',
            project=sample_project,
            defaults={
                'description': f'Implementation tasks for {sample_project.name}',
                'list_type': 'project',
                'priority': 1,
                'created_by': admin_user,
                'start_date': timezone.now().date(),
                'target_completion_date': timezone.now().date() + timedelta(days=30)
            }
        )
        
        if created:
            # Sample project tasks with dependencies
            project_tasks_data = [
                ('Site Survey', 'Conduct initial site survey and assessment', 4.0, 2, 'medium', 1, []),
                ('Design Review', 'Review and approve technical design', 2.0, 1, 'hard', 1, []),
                ('Permit Applications', 'Submit required permits and applications', 1.0, 1, 'medium', 2, ['Site Survey']),
                ('Equipment Procurement', 'Order required equipment and materials', 1.5, 1, 'medium', 2, ['Design Review']),
                ('Site Preparation', 'Prepare installation site', 8.0, 3, 'medium', 2, ['Permit Applications']),
                ('Equipment Installation', 'Install and configure equipment', 16.0, 4, 'hard', 1, ['Equipment Procurement', 'Site Preparation']),
                ('System Testing', 'Test all systems and functionality', 8.0, 2, 'hard', 1, ['Equipment Installation']),
                ('User Training', 'Train end users on system operation', 4.0, 2, 'medium', 3, ['System Testing']),
                ('Documentation', 'Complete all project documentation', 3.0, 1, 'medium', 3, ['System Testing']),
                ('Final Inspection', 'Conduct final inspection and sign-off', 2.0, 2, 'medium', 1, ['User Training', 'Documentation']),
            ]
            
            # Create tasks
            created_tasks = {}
            for title, description, hours, team_size, difficulty, priority, dependencies in project_tasks_data:
                task = Task.objects.create(
                    title=title,
                    description=description,
                    task_list=project_list,
                    allotted_time=Decimal(str(hours)),
                    team_size=team_size,
                    difficulty=difficulty,
                    priority=priority,
                    created_by=admin_user,
                    due_date=timezone.now().date() + timedelta(days=30)
                )
                created_tasks[title] = task
            
            # Add dependencies
            for title, description, hours, team_size, difficulty, priority, dependencies in project_tasks_data:
                if dependencies:
                    task = created_tasks[title]
                    for dep_title in dependencies:
                        if dep_title in created_tasks:
                            task.depends_on.add(created_tasks[dep_title])
            
            print(f"Sample project tasks created for '{sample_project.name}'!")
        
    except Exception as e:
        print(f"Error creating sample project tasks: {str(e)}")
