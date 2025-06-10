# helpdesk/models/data_creation.py - Default Data Creation Functions

from django.utils import timezone
from datetime import timedelta

def create_default_queues():
    """Create default helpdesk queues"""
    from .base import Queue
    
    try:
        default_queues = [
            {
                'title': 'General Support',
                'slug': 'general',
                'description': 'General support requests and questions',
                'allow_public_submission': True,
                'escalate_days': 3,
                'sla_response_time': timedelta(hours=4),
                'sla_resolution_time': timedelta(days=2),
            },
            {
                'title': 'Technical Issues',
                'slug': 'technical',
                'description': 'Technical problems and bug reports',
                'allow_public_submission': True,
                'escalate_days': 1,
                'sla_response_time': timedelta(hours=2),
                'sla_resolution_time': timedelta(hours=24),
            },
            {
                'title': 'Billing Support',
                'slug': 'billing',
                'description': 'Billing questions and account issues',
                'allow_public_submission': True,
                'escalate_days': 2,
                'sla_response_time': timedelta(hours=8),
                'sla_resolution_time': timedelta(days=3),
            },
            {
                'title': 'Feature Requests',
                'slug': 'features',
                'description': 'New feature requests and enhancements',
                'allow_public_submission': True,
                'escalate_days': 7,
                'sla_response_time': timedelta(days=1),
                'sla_resolution_time': timedelta(days=14),
            },
            {
                'title': 'Internal IT',
                'slug': 'internal',
                'description': 'Internal IT support for staff',
                'allow_public_submission': False,
                'escalate_days': 1,
                'sla_response_time': timedelta(hours=4),
                'sla_resolution_time': timedelta(days=1),
            }
        ]
        
        created_count = 0
        for queue_data in default_queues:
            queue, created = Queue.objects.get_or_create(
                slug=queue_data['slug'],
                defaults=queue_data
            )
            if created:
                created_count += 1
                print(f"Created queue: {queue.title}")
        
        print(f"Created {created_count} default queues")
        return created_count
        
    except Exception as e:
        print(f"Error creating default queues: {str(e)}")
        return 0

def create_default_email_templates():
    """Create default email templates"""
    from .templates import EmailTemplate
    
    try:
        default_templates = [
            {
                'template_name': 'New Ticket Notification',
                'template_type': 'new_ticket',
                'subject': '(New Ticket)',
                'heading': 'New Support Ticket Created',
                'plain_text': '''Hello,

A new support ticket has been created:

Ticket #: {{ ticket.ticket }}
Title: {{ ticket.title }}
Queue: {{ queue.title }}
Priority: {{ ticket.get_priority_display }}
Status: {{ ticket.get_status_display }}

Description:
{{ ticket.description }}

You can view this ticket at: {{ ticket.staff_url }}

Best regards,
{{ queue.title }} Team''',
                'html': '''<h2>New Support Ticket Created</h2>
<p>A new support ticket has been created:</p>
<ul>
<li><strong>Ticket #:</strong> {{ ticket.ticket }}</li>
<li><strong>Title:</strong> {{ ticket.title }}</li>
<li><strong>Queue:</strong> {{ queue.title }}</li>
<li><strong>Priority:</strong> {{ ticket.get_priority_display }}</li>
<li><strong>Status:</strong> {{ ticket.get_status_display }}</li>
</ul>
<p><strong>Description:</strong></p>
<p>{{ ticket.description|linebreaks }}</p>
<p><a href="{{ ticket.staff_url }}">View Ticket</a></p>''',
            },
            {
                'template_name': 'Ticket Updated',
                'template_type': 'updated_ticket',
                'subject': '(Updated)',
                'heading': 'Ticket Updated',
                'plain_text': '''Hello,

Your support ticket has been updated:

Ticket #: {{ ticket.ticket }}
Title: {{ ticket.title }}
Status: {{ ticket.get_status_display }}

{% if comment %}
Update:
{{ comment }}
{% endif %}

You can view this ticket at: {{ ticket.ticket_url }}

Best regards,
{{ queue.title }} Team''',
                'html': '''<h2>Ticket Updated</h2>
<p>Your support ticket has been updated:</p>
<ul>
<li><strong>Ticket #:</strong> {{ ticket.ticket }}</li>
<li><strong>Title:</strong> {{ ticket.title }}</li>
<li><strong>Status:</strong> {{ ticket.get_status_display }}</li>
</ul>
{% if comment %}
<p><strong>Update:</strong></p>
<p>{{ comment|linebreaks }}</p>
{% endif %}
<p><a href="{{ ticket.ticket_url }}">View Ticket</a></p>''',
            },
            {
                'template_name': 'Ticket Resolved',
                'template_type': 'resolved_ticket',
                'subject': '(Resolved)',
                'heading': 'Ticket Resolved',
                'plain_text': '''Hello,

Your support ticket has been resolved:

Ticket #: {{ ticket.ticket }}
Title: {{ ticket.title }}

{% if resolution %}
Resolution:
{{ resolution }}
{% endif %}

If you are satisfied with this resolution, no further action is needed. If you need additional assistance, please reply to this email or create a new ticket.

You can view this ticket at: {{ ticket.ticket_url }}

Best regards,
{{ queue.title }} Team''',
                'html': '''<h2>Ticket Resolved</h2>
<p>Your support ticket has been resolved:</p>
<ul>
<li><strong>Ticket #:</strong> {{ ticket.ticket }}</li>
<li><strong>Title:</strong> {{ ticket.title }}</li>
</ul>
{% if resolution %}
<p><strong>Resolution:</strong></p>
<p>{{ resolution|linebreaks }}</p>
{% endif %}
<p>If you are satisfied with this resolution, no further action is needed. If you need additional assistance, please reply to this email or create a new ticket.</p>
<p><a href="{{ ticket.ticket_url }}">View Ticket</a></p>''',
            }
        ]
        
        created_count = 0
        for template_data in default_templates:
            template, created = EmailTemplate.objects.get_or_create(
                template_name=template_data['template_name'],
                defaults=template_data
            )
            if created:
                created_count += 1
                print(f"Created email template: {template.template_name}")
        
        print(f"Created {created_count} default email templates")
        return created_count
        
    except Exception as e:
        print(f"Error creating default email templates: {str(e)}")
        return 0

def create_default_preset_replies():
    """Create default preset replies"""
    from .templates import PreSetReply
    
    try:
        default_replies = [
            {
                'name': 'More Information Needed',
                'reply_type': 'information',
                'body': '''Hello {{ ticket.submitter_name|default:"" }},

Thank you for contacting {{ queue.title }}.

To better assist you with your request, we need some additional information:

- [Please specify what information is needed]

Once we receive this information, we'll be able to provide you with a more detailed response.

Best regards,
{{ user.get_full_name|default:user.username }}
{{ queue.title }} Team''',
                'is_public': True,
            },
            {
                'name': 'Issue Under Investigation',
                'reply_type': 'update',
                'body': '''Hello {{ ticket.submitter_name|default:"" }},

Thank you for reporting this issue. We have received your request and our technical team is currently investigating the problem.

We will keep you updated on our progress and expect to have more information within [timeframe].

If you have any additional details that might help with our investigation, please don't hesitate to share them.

Best regards,
{{ user.get_full_name|default:user.username }}
{{ queue.title }} Team''',
                'is_public': True,
            },
            {
                'name': 'Escalated to Development Team',
                'reply_type': 'escalation',
                'body': '''Hello {{ ticket.submitter_name|default:"" }},

Your issue has been escalated to our development team for further investigation. This typically indicates that the issue may require code changes or additional technical expertise.

We will keep you informed of our progress. Development team reviews are typically completed within [timeframe].

Thank you for your patience.

Best regards,
{{ user.get_full_name|default:user.username }}
{{ queue.title }} Team''',
                'is_public': True,
            },
            {
                'name': 'Resolved - Please Test',
                'reply_type': 'resolution',
                'body': '''Hello {{ ticket.submitter_name|default:"" }},

We believe we have resolved the issue you reported. Please test the solution and let us know if you continue to experience any problems.

Resolution Details:
[Please describe what was done to resolve the issue]

If the issue persists or you have any questions about this resolution, please reply to this email.

Best regards,
{{ user.get_full_name|default:user.username }}
{{ queue.title }} Team''',
                'is_public': True,
            },
            {
                'name': 'Closing Due to No Response',
                'reply_type': 'closure',
                'body': '''Hello {{ ticket.submitter_name|default:"" }},

We have not received a response to our previous communications regarding this support ticket. We are now closing this ticket.

If you still need assistance with this issue, please reply to this email or create a new support ticket, and we'll be happy to help.

Best regards,
{{ user.get_full_name|default:user.username }}
{{ queue.title }} Team''',
                'is_public': True,
                'auto_close_ticket': True,
            }
        ]
        
        created_count = 0
        for reply_data in default_replies:
            reply, created = PreSetReply.objects.get_or_create(
                name=reply_data['name'],
                defaults=reply_data
            )
            if created:
                created_count += 1
                print(f"Created preset reply: {reply.name}")
        
        print(f"Created {created_count} default preset replies")
        return created_count
        
    except Exception as e:
        print(f"Error creating default preset replies: {str(e)}")
        return 0

def create_default_kb_content():
    """Create default knowledge base content"""
    from .knowledge import KBCategory, KBItem
    
    try:
        # Create categories
        default_kb_categories = [
            {
                'title': 'Getting Started',
                'slug': 'getting-started',
                'description': 'Basic information to get you started',
                'icon': 'fa-play-circle',
                'color': '#28a745',
                'sort_order': 1,
            },
            {
                'title': 'Frequently Asked Questions',
                'slug': 'faq',
                'description': 'Answers to commonly asked questions',
                'icon': 'fa-question-circle',
                'color': '#007bff',
                'sort_order': 2,
            },
            {
                'title': 'Troubleshooting',
                'slug': 'troubleshooting',
                'description': 'Solutions to common problems',
                'icon': 'fa-wrench',
                'color': '#fd7e14',
                'sort_order': 3,
            },
            {
                'title': 'Account Management',
                'slug': 'account',
                'description': 'Managing your account and settings',
                'icon': 'fa-user-cog',
                'color': '#6f42c1',
                'sort_order': 4,
            },
            {
                'title': 'Billing and Payments',
                'slug': 'billing',
                'description': 'Billing, payments, and subscription information',
                'icon': 'fa-credit-card',
                'color': '#17a2b8',
                'sort_order': 5,
            }
        ]
        
        created_categories = 0
        for category_data in default_kb_categories:
            category, created = KBCategory.objects.get_or_create(
                slug=category_data['slug'],
                defaults=category_data
            )
            if created:
                created_categories += 1
                print(f"Created KB category: {category.title}")
        
        # Create KB items
        try:
            faq_category = KBCategory.objects.get(slug='faq')
            getting_started_category = KBCategory.objects.get(slug='getting-started')
            
            default_kb_items = [
                {
                    'category': getting_started_category,
                    'title': 'How to Submit a Support Ticket',
                    'question': 'How do I submit a support ticket?',
                    'answer': '''To submit a support ticket:

1. Visit our support portal
2. Click "Submit New Ticket"
3. Choose the appropriate queue for your issue
4. Fill in the ticket title and description
5. Provide as much detail as possible about your issue
6. Click "Submit Ticket"

You will receive an email confirmation with your ticket number.''',
                    'tags': 'ticket, submit, support, help',
                    'is_featured': True,
                },
                {
                    'category': faq_category,
                    'title': 'How Long Until I Get a Response?',
                    'question': 'How long does it take to get a response to my ticket?',
                    'answer': '''Response times depend on the queue and priority of your ticket:

- Technical Issues: 2 hours
- General Support: 4 hours  
- Billing Support: 8 hours
- Feature Requests: 1 day

These are our target response times. Critical issues are prioritized and may receive faster responses.''',
                    'tags': 'response, time, sla, support',
                    'is_featured': True,
                },
                {
                    'category': faq_category,
                    'title': 'How to Check Ticket Status',
                    'question': 'How can I check the status of my ticket?',
                    'answer': '''You can check your ticket status in several ways:

1. Check the email confirmation you received when submitting the ticket
2. Visit our support portal and search for your ticket number
3. Reply to any email correspondence about your ticket
4. Use the ticket tracking link provided in your confirmation email

Your ticket status will be one of: Open, In Progress, Resolved, or Closed.''',
                    'tags': 'status, check, ticket, tracking',
                },
            ]
            
            created_items = 0
            for item_data in default_kb_items:
                # Generate slug from title
                from django.utils.text import slugify
                item_data['slug'] = slugify(item_data['title'])
                
                item, created = KBItem.objects.get_or_create(
                    slug=item_data['slug'],
                    defaults=item_data
                )
                if created:
                    created_items += 1
                    print(f"Created KB item: {item.title}")
            
            print(f"Created {created_categories} KB categories and {created_items} KB items")
            return created_categories + created_items
        
        except KBCategory.DoesNotExist:
            print("KB categories not found, skipping KB items creation")
            return created_categories
        
    except Exception as e:
        print(f"Error creating default KB content: {str(e)}")
        return 0

def create_default_custom_fields():
    """Create default custom fields"""
    from .customfields import CustomField
    
    try:
        default_custom_fields = [
            {
                'name': 'customer_id',
                'label': 'Customer ID',
                'data_type': 'varchar',
                'max_length': 50,
                'help_text': 'Customer account ID for billing reference',
                'field_group': 'business',
                'staff_only': True,
                'ordering': 10,
            },
            {
                'name': 'affected_system',
                'label': 'Affected System',
                'data_type': 'list',
                'list_values': '''Production
Staging
Development
Testing''',
                'help_text': 'Which system is affected by this issue?',
                'field_group': 'technical',
                'ordering': 20,
            },
            {
                'name': 'error_code',
                'label': 'Error Code',
                'data_type': 'varchar',
                'max_length': 20,
                'help_text': 'Error code if applicable',
                'field_group': 'technical',
                'ordering': 30,
            },
            {
                'name': 'business_impact',
                'label': 'Business Impact',
                'data_type': 'list',
                'list_values': '''High - Business Critical
Medium - Important Feature
Low - Minor Issue
None - Enhancement''',
                'help_text': 'What is the business impact of this issue?',
                'field_group': 'business',
                'required': True,
                'ordering': 40,
            }
        ]
        
        created_count = 0
        for field_data in default_custom_fields:
            field, created = CustomField.objects.get_or_create(
                name=field_data['name'],
                defaults=field_data
            )
            if created:
                created_count += 1
                print(f"Created custom field: {field.label}")
        
        print(f"Created {created_count} default custom fields")
        return created_count
        
    except Exception as e:
        print(f"Error creating default custom fields: {str(e)}")
        return 0

def create_sample_tickets():
    """Create sample tickets for demonstration"""
    from .tickets import Ticket
    from .communication import FollowUp
    from .base import Queue
    
    try:
        # Get default queues
        try:
            general_queue = Queue.objects.get(slug='general')
            tech_queue = Queue.objects.get(slug='technical')
        except Queue.DoesNotExist:
            print("Default queues not found. Please run create_default_queues() first.")
            return 0
        
        # Get admin user
        try:
            from hr.models import Worker
            admin_user = Worker.objects.filter(is_staff=True).first()
        except:
            admin_user = None
        
        # Sample tickets
        sample_tickets = [
            {
                'title': 'Unable to Login to Account',
                'queue': general_queue,
                'description': '''I'm having trouble logging into my account. I've tried resetting my password multiple times but I'm still unable to access my account.

Steps I've tried:
1. Password reset via email
2. Clearing browser cache
3. Trying different browsers

Error message: "Invalid credentials"

Please help me regain access to my account.''',
                'submitter_email': 'john.doe@example.com',
                'submitter_name': 'John Doe',
                'priority': 2,
                'ticket_type': 'support',
                'urgency': 3,
            },
            {
                'title': 'Application Crashing on Startup',
                'queue': tech_queue,
                'description': '''The application crashes immediately upon startup. This started happening after the latest update.

Environment: Windows 10, Version 2.1.3
Error Code: 0x80004005

Steps to reproduce:
1. Double-click application icon
2. Splash screen appears briefly
3. Application closes with error dialog

This is affecting our daily operations. Please investigate urgently.''',
                'submitter_email': 'sarah.smith@company.com',
                'submitter_name': 'Sarah Smith',
                'priority': 1,
                'ticket_type': 'bug',
                'urgency': 2,
                'assigned_to': admin_user,
            },
            {
                'title': 'Request for Additional Storage Space',
                'queue': general_queue,
                'description': '''Our team is approaching the storage limit on our current plan. We would like to upgrade our storage allocation.

Current usage: 95% of 100GB
Requested: 500GB total storage

Please let me know:
1. Pricing for the upgrade
2. How long the upgrade takes
3. If there's any downtime involved

Thank you!''',
                'submitter_email': 'manager@startup.com',
                'submitter_name': 'Alex Manager',
                'priority': 3,
                'ticket_type': 'change',
                'urgency': 4,
                'status': Ticket.RESOLVED_STATUS,
            }
        ]
        
        created_count = 0
        for ticket_data in sample_tickets:
            # Set created time to something recent
            ticket_data['created'] = timezone.now() - timedelta(days=2)
            
            ticket = Ticket.objects.create(**ticket_data)
            created_count += 1
            
            # Add some follow-ups for demonstration
            if ticket.title == 'Unable to Login to Account':
                FollowUp.objects.create(
                    ticket=ticket,
                    title='Initial Response',
                    comment='Thank you for contacting support. We are looking into your login issue and will respond within 4 hours.',
                    user=admin_user,
                    public=True,
                    followup_type='comment',
                    date=ticket.created + timedelta(hours=1)
                )
            
            elif ticket.title == 'Application Crashing on Startup':
                FollowUp.objects.create(
                    ticket=ticket,
                    title='Ticket Assigned',
                    comment='This ticket has been assigned to our development team for investigation.',
                    user=admin_user,
                    public=False,
                    followup_type='assignment',
                    date=ticket.created + timedelta(minutes=30)
                )
            
            elif ticket.title == 'Request for Additional Storage Space':
                FollowUp.objects.create(
                    ticket=ticket,
                    title='Storage Upgrade Completed',
                    comment='Your storage has been upgraded to 500GB. The change is now active and you should see the additional space available in your dashboard.',
                    user=admin_user,
                    public=True,
                    followup_type='resolution',
                    new_status=Ticket.RESOLVED_STATUS,
                    date=ticket.created + timedelta(days=1)
                )
                # Update ticket resolution
                ticket.resolution = 'Storage upgraded to 500GB as requested. No downtime was required.'
                ticket.resolution_date = ticket.created + timedelta(days=1)
                ticket.save()
            
            print(f"Created sample ticket: {ticket.title}")
        
        print(f"Created {created_count} sample tickets")
        return created_count
        
    except Exception as e:
        print(f"Error creating sample tickets: {str(e)}")
        return 0

def create_default_helpdesk_data():
    """Create all default helpdesk data"""
    print("Creating default helpdesk data...")
    
    total_created = 0
    total_created += create_default_queues()
    total_created += create_default_email_templates()
    total_created += create_default_preset_replies()
    total_created += create_default_kb_content()
    total_created += create_default_custom_fields()
    
    print(f"Default helpdesk data creation complete! Created {total_created} items total.")
    return total_created