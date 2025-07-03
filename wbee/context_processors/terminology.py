from django.conf import settings


def terminology(request):
    """Add business-specific terminology to the context."""
    defaults = {
        'client_plural': 'Clients',
        'client_singular': 'Client',
        'location_plural': 'Locations',
        'location_singular': 'Location',
        'project_plural': 'Projects',
        'project_singular': 'Project',
        'material_plural': 'Materials',
        'material_singular': 'Material',
    }

    user = getattr(request, 'user', None)
    category = None
    if user and hasattr(user, 'company') and user.company:
        category = getattr(user.company, 'business_category', None)
    if category:
        defaults.update({
            'client_plural': category.client_term,
            'client_singular': category.client_term_singular,
            'location_plural': category.location_term,
            'location_singular': category.location_term_singular,
            'project_plural': category.project_term,
            'project_singular': category.project_term_singular,
            'material_plural': category.material_term,
            'material_singular': category.material_term_singular,
        })
        if category.material_type_nicknames:
            for key, name in category.material_type_nicknames.items():
                defaults[f'material_{key}_term'] = name
    return {'TERMINOLOGY': defaults}
