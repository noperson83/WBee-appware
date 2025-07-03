from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def term(context, key, plural=False):
    terms = context.get('TERMINOLOGY', {})
    suffix = '_plural' if plural else '_singular'
    return terms.get(f'{key}{suffix}', key.title() + ('s' if plural else ''))
