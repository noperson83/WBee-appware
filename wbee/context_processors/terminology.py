from django.conf import settings


def terminology(request):
    """Add business-specific terminology to the context."""
    defaults = {
        'client_plural': 'Clients',
        'client_singular': 'Client',
        'client_synonyms': [],
        'location_plural': 'Locations',
        'location_singular': 'Location',
        'project_plural': 'Projects',
        'project_singular': 'Project',
        'material_plural': 'Materials',
        'material_singular': 'Material',
    }

    user = getattr(request, 'user', None)
    category = None
    config = None
    if user and hasattr(user, 'company') and user.company:
        category = getattr(user.company, 'business_category', None)
        config = getattr(user.company, 'business_config', None)
    if category:
        defaults.update({
            'client_plural': category.client_term,
            'client_singular': category.client_term_singular,
            'client_synonyms': category.client_synonyms,
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
    if config:
        aliases = {
            f"{a.app_label}.{a.model}.{a.field}": a.alias
            for a in config.terminology_aliases.all()
        }
        if aliases:
            defaults['aliases'] = aliases
    return {'TERMINOLOGY': defaults}
