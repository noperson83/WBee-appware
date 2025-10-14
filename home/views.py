# home/views.py
"""
Improved dashboard views to match the original app layout.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import FieldError
from django import forms
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


# Dashboard status helpers
ACTIVE_PROJECT_STATUSES = ["active", "installing"]
ACTIVE_TASK_STATUSES = ["todo", "in_progress", "review", "blocked"]
ACTIVE_EVENT_STATUSES = ["confirmed", "tentative", "draft", "rescheduled"]
ACTIVE_ASSET_STATUSES = ["available", "in_use", "assigned", "active"]


def _user_can_view_company_data(user):
    """Return True when the user should see company-wide metrics."""

    privileged_roles = {
        "admin",
        "project_manager",
        "supervisor",
        "office_manager",
    }

    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True

    has_role = getattr(user, "has_role", None)
    if callable(has_role):
        if any(has_role(role) for role in privileged_roles):
            return True

    primary_role = getattr(user, "role", None)
    if primary_role in privileged_roles:
        return True

    return False


def _filter_for_company(queryset, user, field_name="company", include_null=False):
    """Safely filter a queryset for the user's company if available."""

    user_company = getattr(user, "company", None)
    if user_company:
        company_filter = Q(**{field_name: user_company})
        if include_null:
            return queryset.filter(company_filter | Q(**{f"{field_name}__isnull": True}))
        return queryset.filter(company_filter)
    return queryset

class ContactForm(forms.Form):
    from_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    subject = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))

@login_required
def index(request):
    """
    Enhanced dashboard view matching the original app layout.
    """
    
    # Initialize all context variables
    context = {
        'user': request.user,
        'scheduled_events': [],
        'priority_tasks': [],
        'tools_assigned': [],
        'recent_projects': [],
        'upcoming_deadlines': [],
        'calendar_events': [],
        'dashboard_stats': {},
        
        # Keep backward compatibility
        'worker_detail': [],
        'worker_project_list': [],
        'project_event_list': [],
        'ladder_list': [],
        'vehicle_list': [],
        'tool_list': [],
        'power_tool_list': [],
        'fiber_list': [],
        'tester_list': [],
        'asset_groups': [],
    }
    
    # Load dashboard data
    try:
        context.update(load_enhanced_dashboard_data(request.user))
    except Exception as e:
        logger.error(f"Error loading dashboard data: {e}")
    
    return render(request, 'home/home.html', context)


def load_enhanced_dashboard_data(user):
    """
    Load enhanced dashboard data matching the original app structure.
    """
    data = {}
    
    # Load scheduled events (like the original screenshot)
    data['scheduled_events'] = load_scheduled_events(user)
    
    # Load tools/assets (right sidebar)
    data['tools_assigned'] = load_user_tools(user)
    
    # Load projects
    data['recent_projects'] = load_recent_projects(user)
    
    # Load calendar events for mini calendar
    data['calendar_events'] = load_calendar_events(user)
    
    # Load priority tasks/todo items
    data['priority_tasks'] = load_priority_tasks(user)
    
    # Dashboard statistics
    data['dashboard_stats'] = load_dashboard_stats(user)
    
    # Keep backward compatibility
    data.update(load_backward_compatibility_data(user))
    
    return data


def load_scheduled_events(user):
    """Load scheduled events like in the original screenshot."""
    events = []
    
    try:
        # Try to load from schedule app
        from schedule.models import Event
        
        upcoming_events = Event.objects.filter(
            Q(workers=user) |
            Q(lead=user) |
            Q(creator=user) |
            Q(project__team_members=user) |
            Q(project__team_leads=user) |
            Q(project__project_manager=user),
            start__gte=timezone.now(),
            start__lte=timezone.now() + timedelta(days=30),
            status__in=ACTIVE_EVENT_STATUSES,
        ).select_related('project').distinct()

        upcoming_events = _filter_for_company(
            upcoming_events, user, field_name='project__company'
        ).order_by('start')[:5]
        
        for event in upcoming_events:
            # Extract job number from title if it exists
            job_number = extract_job_number(event.title if hasattr(event, 'title') else str(event))
            
            events.append({
                'id': event.id,
                'job_number': job_number,
                'title': getattr(event, 'title', str(event)),
                'date': event.start,
                'location': getattr(event, 'location', ''),
                'description': getattr(event, 'description', ''),
                'project': getattr(event, 'project', None),
                'color_class': get_event_color_class(event),
            })
            
    except (ImportError, AttributeError) as e:
        logger.debug(f"Schedule app not available: {e}")
        
        # Create sample events if no schedule app
        events = create_sample_events()
    
    return events


def load_user_tools(user):
    """Load user's assigned tools/assets for the Tools sidebar."""
    tools = []
    
    try:
        from asset.models import Asset

        user_assets = Asset.objects.filter(
            Q(assigned_worker=user) |
            Q(assignments__assigned_to_worker=user, assignments__is_active=True),
            is_active=True,
            status__in=ACTIVE_ASSET_STATUSES,
        ).select_related('category').order_by('category__name', 'name').distinct()

        user_assets = _filter_for_company(user_assets, user)
        
        # Group by category like in the original
        current_category = None
        category_group = None
        
        for asset in user_assets:
            category = getattr(asset.category, 'name', getattr(asset, 'asset_type', 'Other'))
            
            if category != current_category:
                if category_group:
                    tools.append(category_group)
                
                category_group = {
                    'category': category,
                    'items': [],
                    'icon': get_category_icon(category),
                    'color': get_category_color(category)
                }
                current_category = category
            
            if category_group:
                category_group['items'].append({
                    'id': asset.uuid if hasattr(asset, 'uuid') else asset.id,
                    'name': asset.name,
                    'asset_number': getattr(asset, 'asset_number', ''),
                    'location': getattr(asset, 'location', ''),
                    'status': getattr(asset, 'status', 'active'),
                })
        
        # Add the last group
        if category_group:
            tools.append(category_group)
            
    except (ImportError, AttributeError) as e:
        logger.debug(f"Asset app not available: {e}")
        tools = create_sample_tools()
    
    return tools


def load_recent_projects(user):
    """Load recent projects for the user."""
    projects = []
    
    try:
        from project.models import Project
        
        user_projects = Project.objects.filter(
            Q(team_members=user) |
            Q(team_leads=user) |
            Q(project_manager=user),
            status__in=ACTIVE_PROJECT_STATUSES,
        ).distinct()

        user_projects = _filter_for_company(user_projects, user).order_by('-updated_at')[:5]
        
        for project in user_projects:
            projects.append({
                'id': project.id,
                'name': project.name,
                'job_number': getattr(project, 'job_num', ''),
                'status': getattr(project, 'status', 'active'),
                'client': getattr(project, 'client', None),
                'progress': calculate_project_progress(project),
                'updated_at': project.updated_at,
            })
            
    except (ImportError, AttributeError) as e:
        logger.debug(f"Project app not available: {e}")
    
    return projects


def load_calendar_events(user):
    """Load calendar events for mini calendar widget."""
    events = []
    
    try:
        from schedule.models import Event
        
        # Get events for current month
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        monthly_events = Event.objects.filter(
            Q(workers=user) |
            Q(lead=user) |
            Q(creator=user) |
            Q(project__team_members=user) |
            Q(project__team_leads=user) |
            Q(project__project_manager=user),
            start__date__gte=start_of_month,
            start__date__lte=end_of_month,
            status__in=ACTIVE_EVENT_STATUSES,
        ).distinct()

        monthly_events = _filter_for_company(
            monthly_events, user, field_name='project__company'
        ).order_by('start')
        
        for event in monthly_events:
            events.append({
                'date': event.start.date(),
                'title': getattr(event, 'title', str(event)),
                'time': event.start.time(),
                'type': getattr(event, 'event_type', 'general'),
            })
            
    except (ImportError, AttributeError):
        pass
    
    return events


def load_priority_tasks(user):
    """Load priority tasks/todo items."""
    tasks = []
    
    try:
        # Try to load from a todo/task app if it exists
        from todo.models import Task
        
        priority_tasks = Task.objects.filter(
            assigned_to=user,
            completed=False,
            status__in=ACTIVE_TASK_STATUSES,
        )

        priority_tasks = _filter_for_company(
            priority_tasks,
            user,
            field_name='task_list__project__company',
            include_null=True,
        ).order_by('-priority', 'due_date')[:5]

        for task in priority_tasks:
            tasks.append({
                'id': task.id,
                'title': task.title,
                'description': getattr(task, 'description', ''),
                'due_date': getattr(task, 'due_date', None),
                'priority': getattr(task, 'priority', 'normal'),
                'project': getattr(task, 'project', None),
            })

    except (ImportError, AttributeError, FieldError) as exc:
        if isinstance(exc, FieldError):
            logger.debug(f"Task filtering failed: {exc}")
        # Create sample tasks if no todo app
        tasks = create_sample_tasks()
    
    return tasks


def load_dashboard_stats(user):
    """Load dashboard statistics."""
    stats = {
        'total_assets': 0,
        'active_projects': 0,
        'pending_tasks': 0,
        'upcoming_events': 0,
    }
    
    can_view_company = _user_can_view_company_data(user)

    try:
        from asset.models import Asset

        asset_qs = Asset.objects.filter(
            is_active=True,
            status__in=ACTIVE_ASSET_STATUSES,
        )

        if can_view_company:
            asset_qs = _filter_for_company(asset_qs, user)
        else:
            asset_qs = asset_qs.filter(
                Q(assigned_worker=user)
                | Q(assignments__assigned_to_worker=user, assignments__is_active=True)
            ).distinct()
            asset_qs = _filter_for_company(asset_qs, user)

        stats['total_assets'] = asset_qs.count()
    except (ImportError, AttributeError, FieldError) as exc:
        if isinstance(exc, FieldError):
            logger.debug(f"Asset filtering failed: {exc}")
        pass

    try:
        from todo.models import Task
        task_qs = Task.objects.filter(
            assigned_to=user,
            status__in=ACTIVE_TASK_STATUSES,
            completed=False,
        )

        stats['pending_tasks'] = _filter_for_company(
            task_qs,
            user,
            field_name='task_list__project__company',
            include_null=True,
        ).count()
    except (ImportError, AttributeError, FieldError) as exc:
        if isinstance(exc, FieldError):
            logger.debug(f"Task stats filtering failed: {exc}")
        pass

    try:
        from project.models import Project
        project_qs = Project.objects.filter(status__in=ACTIVE_PROJECT_STATUSES)

        project_qs = _filter_for_company(project_qs, user)

        if not can_view_company:
            project_qs = project_qs.filter(
                Q(team_members=user) | Q(team_leads=user) | Q(project_manager=user)
            )

        stats['active_projects'] = project_qs.distinct().count()
    except (ImportError, AttributeError, FieldError) as exc:
        if isinstance(exc, FieldError):
            logger.debug(f"Project filtering failed: {exc}")
        pass

    try:
        from schedule.models import Event
        event_qs = Event.objects.filter(
            start__gte=timezone.now(),
            start__lte=timezone.now() + timedelta(days=7),
            status__in=ACTIVE_EVENT_STATUSES,
        )

        if can_view_company:
            event_qs = _filter_for_company(
                event_qs, user, field_name='project__company'
            )
        else:
            event_qs = event_qs.filter(
                Q(workers=user)
                | Q(lead=user)
                | Q(creator=user)
                | Q(project__team_members=user)
                | Q(project__team_leads=user)
                | Q(project__project_manager=user)
            ).distinct()
            event_qs = _filter_for_company(
                event_qs, user, field_name='project__company'
            )

        stats['upcoming_events'] = event_qs.count()
    except (ImportError, AttributeError, FieldError) as exc:
        if isinstance(exc, FieldError):
            logger.debug(f"Event filtering failed: {exc}")
        pass

    return stats


def load_backward_compatibility_data(user):
    """Load data for backward compatibility with original templates."""
    data = {
        'worker_project_list': [],
        'project_event_list': [],
        'ladder_list': [],
        'vehicle_list': [],
        'tool_list': [],
        'power_tool_list': [],
        'fiber_list': [],
        'tester_list': [],
        'asset_groups': [],
    }
    
    try:
        from asset.models import Asset
        user_assets = Asset.objects.filter(
            Q(assigned_worker=user) |
            Q(assignments__assigned_to_worker=user, assignments__is_active=True),
            is_active=True,
            status__in=ACTIVE_ASSET_STATUSES,
        ).distinct()

        user_assets = _filter_for_company(user_assets, user)
        
        # Original template variables
        data['ladder_list'] = user_assets.filter(asset_type__icontains='ladder')[:10]
        data['vehicle_list'] = user_assets.filter(asset_type__icontains='vehicle')[:10]
        data['tool_list'] = user_assets.filter(asset_type__icontains='tool')[:10]
        data['power_tool_list'] = user_assets.filter(asset_type__icontains='power')[:10]
        data['fiber_list'] = user_assets.filter(asset_type__icontains='fiber')[:10]
        data['tester_list'] = user_assets.filter(asset_type__icontains='test')[:10]
        
        # Asset groups
        asset_categories = {}
        for asset in user_assets:
            category = getattr(asset.category, 'name', getattr(asset, 'asset_type', 'Other'))
            if category not in asset_categories:
                asset_categories[category] = []
            asset_categories[category].append(asset)
        
        data['asset_groups'] = [
            {'title': cat, 'items': items} 
            for cat, items in asset_categories.items()
        ]
        
    except (ImportError, AttributeError):
        pass
    
    try:
        from project.models import Project
        project_qs = Project.objects.filter(
            Q(team_members=user) | Q(team_leads=user) | Q(project_manager=user),
            status__in=ACTIVE_PROJECT_STATUSES,
        ).distinct()

        data['worker_project_list'] = _filter_for_company(project_qs, user)[:10]
    except (ImportError, AttributeError):
        pass
    
    try:
        from schedule.models import Event
        event_qs = Event.objects.filter(
            Q(workers=user) |
            Q(lead=user) |
            Q(creator=user) |
            Q(project__team_members=user) |
            Q(project__team_leads=user) |
            Q(project__project_manager=user),
            start__gte=timezone.now(),
            status__in=ACTIVE_EVENT_STATUSES,
        ).distinct()

        data['project_event_list'] = _filter_for_company(
            event_qs, user, field_name='project__company'
        ).order_by('start')[:10]
    except (ImportError, AttributeError):
        pass
    
    return data


# Utility functions
def extract_job_number(text):
    """Extract job number from text (like '3159' from the screenshot)."""
    import re
    match = re.search(r'\b(\d{4})\b', text)
    return match.group(1) if match else ''


def get_event_color_class(event):
    """Get CSS color class for event based on type."""
    event_type = getattr(event, 'event_type', 'general')
    color_map = {
        'installation': 'info',
        'testing': 'success', 
        'meeting': 'warning',
        'maintenance': 'danger',
        'general': 'primary',
    }
    return color_map.get(event_type, 'primary')


def get_category_icon(category):
    """Get icon for asset category."""
    category_lower = category.lower()
    if 'ladder' in category_lower:
        return 'fas fa-ladder'
    elif 'vehicle' in category_lower:
        return 'fas fa-truck'
    elif 'tool' in category_lower:
        return 'fas fa-tools'
    elif 'test' in category_lower:
        return 'fas fa-vial'
    elif 'fiber' in category_lower:
        return 'fas fa-ethernet'
    else:
        return 'fas fa-box'


def get_category_color(category):
    """Get color for asset category."""
    category_lower = category.lower()
    if 'ladder' in category_lower:
        return 'primary'
    elif 'vehicle' in category_lower:
        return 'success'
    elif 'tool' in category_lower:
        return 'warning'
    elif 'test' in category_lower:
        return 'info'
    elif 'fiber' in category_lower:
        return 'secondary'
    else:
        return 'light'


def calculate_project_progress(project):
    """Calculate project progress percentage."""
    # This would depend on your project model structure
    status = getattr(project, 'status', 'planning')
    progress_map = {
        'planning': 10,
        'active': 50,
        'testing': 80,
        'complete': 100,
        'on_hold': 25,
    }
    return progress_map.get(status, 0)


def create_sample_events():
    """Create sample events when schedule app is not available."""
    today = timezone.now()
    return [
        {
            'job_number': '3159',
            'title': 'Sun City Day 12: Screens Sun City Oro Valley AV',
            'date': today + timedelta(days=1),
            'location': 'Sun City',
            'color_class': 'info',
        },
        {
            'job_number': '3022',
            'title': 'Test all buttons: Test and function Del Sol',
            'date': today + timedelta(days=3),
            'location': 'Del Sol',
            'color_class': 'success',
        },
    ]


def create_sample_tools():
    """Create sample tools when asset app is not available."""
    return [
        {
            'category': 'Ladder',
            'icon': 'fas fa-ladder',
            'color': 'primary',
            'items': [
                {'name': 'AV1200', 'location': 'Truck', 'status': 'active'}
            ]
        }
    ]


def create_sample_tasks():
    """Create sample tasks when todo app is not available."""
    return [
        {
            'title': 'Complete installation documentation',
            'priority': 'high',
            'due_date': timezone.now().date() + timedelta(days=2),
        },
        {
            'title': 'Schedule equipment maintenance',
            'priority': 'medium',
            'due_date': timezone.now().date() + timedelta(days=5),
        },
    ]


def contactView(request):
    """Contact form view."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                subject = form.cleaned_data['subject']
                from_email = form.cleaned_data['from_email'] 
                message = form.cleaned_data['message']
                
                send_mail(
                    subject=f"Contact Form: {subject}",
                    message=f"From: {from_email}\n\n{message}",
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                    recipient_list=[getattr(settings, 'CONTACT_EMAIL', 'admin@example.com')],
                    fail_silently=False
                )
                messages.success(request, 'Message sent successfully!')
                return redirect('home:success')
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
                messages.error(request, 'Failed to send message. Please try again.')
    else:
        form = ContactForm()
    
    return render(request, 'home/contact.html', {'form': form})


def successView(request):
    """Success page."""
    return render(request, 'home/success.html', {
        'message': 'Success! Thank you for your message.'
    })


def schedule_demo(request):
    """Simple demo view showing scheduled events snippet."""
    return render(request, "home/schedule_example.html")


def permission_denied_view(request, exception=None):
    """Render custom 403 page."""
    return render(request, "403.html", status=403)

