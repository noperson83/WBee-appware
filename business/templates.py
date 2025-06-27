# business/templates.py - Modernized Business Templates for Rapid Deployment
"""
Collection of business templates for quick project setup with enhanced structure.
"""

from .models import BusinessConfiguration, BusinessType, ProjectCategory, BusinessTemplate


def create_business_templates():
    """Create all predefined business templates in the database"""
    
    # Create Business Types first
    business_types = {
        'construction': BusinessType.objects.get_or_create(
            slug='construction',
            defaults={
                'name': 'Construction & Contracting',
                'description': 'General contracting, electrical, plumbing, HVAC, and specialized construction services',
                'icon': '🏗️',
                'color': '#fd7e14',
                'typical_project_size': 'large'
            }
        )[0],
        
        'service': BusinessType.objects.get_or_create(
            slug='service',
            defaults={
                'name': 'Service Business',
                'description': 'Professional services, consulting, maintenance, and support services',
                'icon': '🔧',
                'color': '#20c997',
                'typical_project_size': 'medium'
            }
        )[0],
        
        'manufacturing': BusinessType.objects.get_or_create(
            slug='manufacturing',
            defaults={
                'name': 'Manufacturing & Production',
                'description': 'Manufacturing, production, distribution, and related industrial services',
                'icon': '🏭',
                'color': '#6f42c1',
                'typical_project_size': 'large'
            }
        )[0],
        
        'technology': BusinessType.objects.get_or_create(
            slug='technology',
            defaults={
                'name': 'Technology & Software',
                'description': 'Software development, IT services, consulting, and technology solutions',
                'icon': '💻',
                'color': '#0dcaf0',
                'typical_project_size': 'medium'
            }
        )[0],
        
        'retail': BusinessType.objects.get_or_create(
            slug='retail',
            defaults={
                'name': 'Retail & Distribution',
                'description': 'Retail sales, distribution, e-commerce, and related services',
                'icon': '🛍️',
                'color': '#198754',
                'typical_project_size': 'small'
            }
        )[0],
    }
    
    # Create Business Configurations
    configs = {
        'single_project': BusinessConfiguration.objects.get_or_create(
            slug='single-project-based',
            defaults={
                'name': 'Single Company - Project Based',
                'description': 'Traditional single company operating with project-based billing',
                'deployment_type': 'single',
                'billing_model': 'project',
                'default_payment_terms_days': 30,
                'requires_licensing': True,
            }
        )[0],
        
        'collaborative': BusinessConfiguration.objects.get_or_create(
            slug='collaborative-network',
            defaults={
                'name': 'Collaborative Business Network',
                'description': 'Multiple companies working together on shared projects',
                'deployment_type': 'collaborative',
                'billing_model': 'project',
                'enables_shared_workforce': True,
                'enables_shared_clients': True,
                'enables_cross_selling': True,
                'default_payment_terms_days': 15,
            }
        )[0],
        
        'service_hourly': BusinessConfiguration.objects.get_or_create(
            slug='service-hourly-billing',
            defaults={
                'name': 'Service Business - Hourly Billing',
                'description': 'Service-based business with hourly rate billing',
                'deployment_type': 'single',
                'billing_model': 'hourly',
                'default_payment_terms_days': 15,
                'requires_certifications': True,
            }
        )[0],
    }
    
    # Template Definitions with Enhanced Structure
    TEMPLATES = {
        'low_voltage': {
            'name': 'Low Voltage Installation & Security',
            'description': 'Comprehensive template for low voltage contractors including security systems, networking, and AV installations',
            'business_type': business_types['construction'],
            'business_config': configs['single_project'],
            'is_featured': True,
            'template_data': {
                'categories': [
                    {
                        'name': 'Security Devices',
                        'icon': '📱',
                        'color': '#28a745',
                        'description': 'Cameras, sensors, access control devices',
                        'is_billable': True,
                        'default_unit': 'each',
                        'default_markup_percentage': 25.00,
                        'requires_approval': False,
                    },
                    {
                        'name': 'Network Hardware',
                        'icon': '🔧',
                        'color': '#dc3545',
                        'description': 'Switches, routers, cables, and networking equipment',
                        'is_billable': True,
                        'default_unit': 'each',
                        'default_markup_percentage': 20.00,
                    },
                    {
                        'name': 'Software & Licenses',
                        'icon': '💻',
                        'color': '#007bff',
                        'description': 'Security software, monitoring systems, licenses',
                        'is_billable': True,
                        'default_unit': 'license',
                        'default_markup_percentage': 15.00,
                    },
                    {
                        'name': 'Installation Labor',
                        'icon': '👷',
                        'color': '#ffc107',
                        'description': 'Installation, configuration, and setup labor',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 0.00,
                    },
                    {
                        'name': 'Travel & Logistics',
                        'icon': '🚗',
                        'color': '#6c757d',
                        'description': 'Travel time, mileage, and logistics costs',
                        'is_billable': True,
                        'default_unit': 'mile',
                        'default_markup_percentage': 0.00,
                    },
                ],
                'workflow_requirements': {
                    'requires_site_survey': True,
                    'requires_permits': True,
                    'requires_testing': True,
                    'warranty_period_months': 12,
                    'follow_up_required': True,
                },
                'default_settings': {
                    'project_duration_days': 14,
                    'payment_schedule': 'Net 30',
                    'warranty_terms': '1 year parts and labor',
                    'required_certifications': ['Low Voltage License', 'Security Systems License'],
                }
            }
        },
        
        'yard_cleaning': {
            'name': 'Landscaping & Yard Services',
            'description': 'Complete template for landscaping, yard maintenance, and outdoor services',
            'business_type': business_types['service'],
            'business_config': configs['service_hourly'],
            'is_featured': True,
            'template_data': {
                'categories': [
                    {
                        'name': 'Equipment Rental',
                        'icon': '🚜',
                        'color': '#28a745',
                        'description': 'Lawn mowers, trimmers, blowers, and heavy equipment',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 30.00,
                    },
                    {
                        'name': 'Materials & Supplies',
                        'icon': '🌱',
                        'color': '#dc3545',
                        'description': 'Seeds, fertilizer, mulch, plants, and landscaping materials',
                        'is_billable': True,
                        'default_unit': 'bag',
                        'default_markup_percentage': 35.00,
                    },
                    {
                        'name': 'Labor & Services',
                        'icon': '👨‍🌾',
                        'color': '#007bff',
                        'description': 'Landscaping labor, maintenance, and specialized services',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 0.00,
                    },
                    {
                        'name': 'Disposal & Cleanup',
                        'icon': '🗑️',
                        'color': '#ffc107',
                        'description': 'Yard waste disposal, debris removal, cleanup services',
                        'is_billable': True,
                        'default_unit': 'load',
                        'default_markup_percentage': 20.00,
                    },
                    {
                        'name': 'Travel & Transportation',
                        'icon': '🚗',
                        'color': '#6c757d',
                        'description': 'Travel time and transportation costs',
                        'is_billable': True,
                        'default_unit': 'mile',
                        'default_markup_percentage': 0.00,
                    },
                ],
                'workflow_requirements': {
                    'requires_site_assessment': True,
                    'seasonal_considerations': True,
                    'weather_dependent': True,
                    'follow_up_maintenance': True,
                },
                'default_settings': {
                    'project_duration_days': 3,
                    'payment_schedule': 'Net 15',
                    'seasonal_rates': True,
                    'maintenance_contracts_available': True,
                }
            }
        },
        
        'beer_distribution': {
            'name': 'Beverage Distribution',
            'description': 'Template for beer, wine, and beverage distribution businesses',
            'business_type': business_types['retail'],
            'business_config': configs['single_project'],
            'is_featured': False,
            'template_data': {
                'categories': [
                    {
                        'name': 'Beer Products',
                        'icon': '🍺',
                        'color': '#28a745',
                        'description': 'Cases, kegs, and specialty beer products',
                        'is_billable': True,
                        'default_unit': 'case',
                        'default_markup_percentage': 25.00,
                    },
                    {
                        'name': 'Wine & Spirits',
                        'icon': '🍷',
                        'color': '#dc3545',
                        'description': 'Wine bottles, spirits, and premium beverages',
                        'is_billable': True,
                        'default_unit': 'bottle',
                        'default_markup_percentage': 30.00,
                    },
                    {
                        'name': 'Distribution Services',
                        'icon': '🚛',
                        'color': '#007bff',
                        'description': 'Delivery, logistics, and distribution services',
                        'is_billable': True,
                        'default_unit': 'delivery',
                        'default_markup_percentage': 15.00,
                    },
                    {
                        'name': 'Storage & Handling',
                        'icon': '📦',
                        'color': '#ffc107',
                        'description': 'Warehousing, refrigeration, and special handling',
                        'is_billable': True,
                        'default_unit': 'pallet',
                        'default_markup_percentage': 20.00,
                    },
                    {
                        'name': 'Licensing & Compliance',
                        'icon': '📜',
                        'color': '#6c757d',
                        'description': 'Permits, licenses, and compliance fees',
                        'is_billable': True,
                        'default_unit': 'each',
                        'default_markup_percentage': 0.00,
                    },
                ],
                'workflow_requirements': {
                    'requires_liquor_license': True,
                    'age_verification_required': True,
                    'temperature_controlled': True,
                    'inventory_tracking': True,
                    'regulatory_compliance': True,
                },
                'default_settings': {
                    'project_duration_days': 1,
                    'payment_schedule': 'Net 30',
                    'minimum_order_requirements': True,
                    'delivery_schedule': 'Weekly',
                }
            }
        },
        
        'handyman_services': {
            'name': 'General Handyman Services',
            'description': 'Versatile template for handyman and general maintenance services',
            'business_type': business_types['service'],
            'business_config': configs['service_hourly'],
            'is_featured': True,
            'template_data': {
                'categories': [
                    {
                        'name': 'Tools & Equipment',
                        'icon': '🛠️',
                        'color': '#28a745',
                        'description': 'Hand tools, power tools, and specialized equipment',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 20.00,
                    },
                    {
                        'name': 'Materials & Supplies',
                        'icon': '🧰',
                        'color': '#dc3545',
                        'description': 'Hardware, lumber, electrical, plumbing supplies',
                        'is_billable': True,
                        'default_unit': 'each',
                        'default_markup_percentage': 35.00,
                    },
                    {
                        'name': 'Repair Services',
                        'icon': '🔧',
                        'color': '#007bff',
                        'description': 'General repairs, maintenance, and troubleshooting',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 0.00,
                    },
                    {
                        'name': 'Specialty Labor',
                        'icon': '💪',
                        'color': '#ffc107',
                        'description': 'Electrical, plumbing, HVAC, and specialized work',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 0.00,
                    },
                    {
                        'name': 'Emergency Services',
                        'icon': '🚨',
                        'color': '#dc3545',
                        'description': 'After-hours and emergency repair services',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 0.00,
                    },
                ],
                'workflow_requirements': {
                    'flexible_scheduling': True,
                    'emergency_availability': True,
                    'skill_verification': True,
                    'insurance_required': True,
                },
                'default_settings': {
                    'project_duration_days': 1,
                    'payment_schedule': 'Due on completion',
                    'emergency_rate_multiplier': 1.5,
                    'minimum_service_charge': 75.00,
                }
            }
        },
        
        'custom_manufacturing': {
            'name': 'Custom T-Shirt & Apparel',
            'description': 'Template for custom apparel printing and manufacturing',
            'business_type': business_types['manufacturing'],
            'business_config': configs['single_project'],
            'is_featured': False,
            'template_data': {
                'categories': [
                    {
                        'name': 'Blank Apparel',
                        'icon': '👕',
                        'color': '#28a745',
                        'description': 'T-shirts, hoodies, hats, and blank garments',
                        'is_billable': True,
                        'default_unit': 'piece',
                        'default_markup_percentage': 40.00,
                    },
                    {
                        'name': 'Printing Materials',
                        'icon': '🎨',
                        'color': '#dc3545',
                        'description': 'Inks, transfers, vinyl, and printing consumables',
                        'is_billable': True,
                        'default_unit': 'each',
                        'default_markup_percentage': 30.00,
                    },
                    {
                        'name': 'Design Services',
                        'icon': '🖌️',
                        'color': '#007bff',
                        'description': 'Custom design, artwork, and graphic services',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 0.00,
                    },
                    {
                        'name': 'Production Labor',
                        'icon': '⚙️',
                        'color': '#ffc107',
                        'description': 'Printing, cutting, pressing, and finishing labor',
                        'is_billable': True,
                        'default_unit': 'piece',
                        'default_markup_percentage': 0.00,
                    },
                    {
                        'name': 'Packaging & Shipping',
                        'icon': '📦',
                        'color': '#6c757d',
                        'description': 'Packaging materials and shipping services',
                        'is_billable': True,
                        'default_unit': 'order',
                        'default_markup_percentage': 15.00,
                    },
                ],
                'workflow_requirements': {
                    'design_approval_required': True,
                    'sample_approval': True,
                    'quality_control': True,
                    'production_scheduling': True,
                },
                'default_settings': {
                    'project_duration_days': 7,
                    'payment_schedule': '50% deposit, 50% on completion',
                    'minimum_order_quantity': 12,
                    'rush_order_available': True,
                }
            }
        },
        
        'tech_consulting': {
            'name': 'Technology Consulting',
            'description': 'Template for IT consulting and technology services',
            'business_type': business_types['technology'],
            'business_config': configs['service_hourly'],
            'is_featured': True,
            'template_data': {
                'categories': [
                    {
                        'name': 'Consulting Services',
                        'icon': '💼',
                        'color': '#007bff',
                        'description': 'Strategy, planning, and advisory services',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 0.00,
                    },
                    {
                        'name': 'Software Development',
                        'icon': '💻',
                        'color': '#28a745',
                        'description': 'Custom software development and programming',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 0.00,
                    },
                    {
                        'name': 'Infrastructure Services',
                        'icon': '🖥️',
                        'color': '#dc3545',
                        'description': 'Server setup, networking, and IT infrastructure',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 0.00,
                    },
                    {
                        'name': 'Software Licenses',
                        'icon': '📜',
                        'color': '#ffc107',
                        'description': 'Software licenses and subscription services',
                        'is_billable': True,
                        'default_unit': 'license',
                        'default_markup_percentage': 10.00,
                    },
                    {
                        'name': 'Training & Support',
                        'icon': '📚',
                        'color': '#6c757d',
                        'description': 'User training and ongoing support services',
                        'is_billable': True,
                        'default_unit': 'hour',
                        'default_markup_percentage': 0.00,
                    },
                ],
                'workflow_requirements': {
                    'requirements_gathering': True,
                    'technical_documentation': True,
                    'testing_required': True,
                    'user_acceptance_testing': True,
                    'ongoing_support': True,
                },
                'default_settings': {
                    'project_duration_days': 30,
                    'payment_schedule': 'Monthly invoicing',
                    'retainer_available': True,
                    'support_contract_available': True,
                }
            }
        },
    }
    
    # Create the templates in the database
    created_templates = []
    for template_key, template_data in TEMPLATES.items():
        template, created = BusinessTemplate.objects.get_or_create(
            slug=template_key.replace('_', '-'),
            defaults=template_data
        )
        if created:
            created_templates.append(template.name)
            
            # Create associated project categories
            for category_data in template_data['template_data']['categories']:
                ProjectCategory.objects.get_or_create(
                    business_config=template.business_config,
                    business_type=template.business_type,
                    name=category_data['name'],
                    defaults={
                        'slug': category_data['name'].lower().replace(' ', '-').replace('&', 'and'),
                        'description': category_data.get('description', ''),
                        'icon': category_data['icon'],
                        'color': category_data['color'],
                        'is_billable': category_data.get('is_billable', True),
                        'default_unit': category_data.get('default_unit', 'each'),
                        'default_markup_percentage': category_data.get('default_markup_percentage', 0.00),
                        'requires_approval': category_data.get('requires_approval', False),
                    }
                )
    
    return created_templates


# Utility functions for template management
def get_template_by_industry(industry_name):
    """Get templates filtered by industry/business type"""
    try:
        business_type = BusinessType.objects.get(name__icontains=industry_name)
        return BusinessTemplate.objects.filter(
            business_type=business_type,
            is_active=True
        ).order_by('-is_featured', 'name')
    except BusinessType.DoesNotExist:
        return BusinessTemplate.objects.none()


def get_featured_templates():
    """Get all featured templates"""
    return BusinessTemplate.objects.filter(
        is_featured=True,
        is_active=True
    ).order_by('name')


def get_popular_templates(limit=10):
    """Get most popular templates by usage count"""
    return BusinessTemplate.objects.filter(
        is_active=True
    ).order_by('-usage_count')[:limit]
