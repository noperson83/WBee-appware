from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def category_items(project, category_slug):
    """Return project material items for a given category"""
    try:
        return project.get_items_by_category(category_slug)
    except Exception:
        return []

@register.filter
def status_badge(status):
    """Return HTML badge for project status"""
    colors = {
        'prospect': '#FFA500',
        'quoted': '#17a2b8',
        'active': '#28a745',
        'installing': '#007bff',
        'complete': '#6c757d',
        'invoiced': '#fd7e14',
        'paid': '#28a745',
        'cancelled': '#dc3545',
    }
    color = colors.get(status, '#007bff')
    label = str(status).replace('_', ' ').title()
    html = (
        f'<span style="background-color: {color}; color: white; padding: 2px 8px; '
        f'border-radius: 3px; font-size: 11px; font-weight: bold;">{label}</span>'
    )
    return mark_safe(html)

@register.filter
def progress_bar(percent):
    """Return HTML progress bar from a percentage value"""
    try:
        percent = float(percent)
    except (TypeError, ValueError):
        percent = 0
    if percent >= 100:
        color = '#28a745'
    elif percent >= 75:
        color = '#007bff'
    elif percent >= 50:
        color = '#ffc107'
    else:
        color = '#dc3545'
    html = (
        '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
        f'<div style="width: {percent}%; background-color: {color}; height: 20px; '
        'border-radius: 3px; text-align: center; line-height: 20px; color: white; '
        'font-size: 11px; font-weight: bold;">'
        f'{int(percent)}%'
        '</div></div>'
    )
    return mark_safe(html)

@register.filter
def financial_summary(project):
    """Return HTML summary of contract value and margin"""
    if getattr(project, 'contract_value', None):
        color = '#28a745' if project.is_profitable else '#dc3545'
        html = (
            '<div style="font-size: 11px;">'
            f'<strong>${project.contract_value:,.0f}</strong><br>'
            f'<span style="color: {color};">{project.profit_margin:.1f}% margin</span>'
            '</div>'
        )
        return mark_safe(html)
    return '—'

@register.filter
def due_indicator(project):
    """Return HTML indicator if project is overdue or due soon"""
    if getattr(project, 'is_overdue', False):
        return mark_safe('<span style="color: #dc3545; font-weight: bold;">⚠ OVERDUE</span>')
    days = getattr(project, 'days_until_due', None)
    if days is not None and days <= 7:
        return mark_safe('<span style="color: #ffc107; font-weight: bold;">⚡ Due Soon</span>')
    return ''
