# helpdesk/models/__init__.py - Import all models for the helpdesk app

# Base models (Queue)
from .base import Queue

# Ticket models
from .tickets import Ticket, TicketDependency, TicketCC

# Communication models
from .communication import FollowUp, TicketChange, Attachment

# Template models
from .templates import PreSetReply, EmailTemplate, EscalationExclusion

# Knowledge base models
from .knowledge import KBCategory, KBItem

# Utility models
from .utils import SavedSearch, UserSettings, IgnoreEmail

# Custom field models
from .customfields import CustomField, TicketCustomFieldValue

# Data creation functions
from .data_creation import (
    create_default_helpdesk_data,
    create_sample_tickets,
    create_default_queues,
    create_default_email_templates,
    create_default_preset_replies,
    create_default_kb_content,
    create_default_custom_fields
)

# Make all models available at package level
__all__ = [
    # Base
    'Queue',
    
    # Tickets
    'Ticket',
    'TicketDependency', 
    'TicketCC',
    
    # Communication
    'FollowUp',
    'TicketChange',
    'Attachment',
    
    # Templates
    'PreSetReply',
    'EmailTemplate',
    'EscalationExclusion',
    
    # Knowledge Base
    'KBCategory',
    'KBItem',
    
    # Utilities
    'SavedSearch',
    'UserSettings',
    'IgnoreEmail',
    
    # Custom Fields
    'CustomField',
    'TicketCustomFieldValue',
    
    # Data Creation Functions
    'create_default_helpdesk_data',
    'create_sample_tickets',
    'create_default_queues',
    'create_default_email_templates',
    'create_default_preset_replies',
    'create_default_kb_content',
    'create_default_custom_fields',
]
