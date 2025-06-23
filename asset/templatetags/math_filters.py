from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        return value - arg
    except TypeError:
        try:
            return float(value) - float(arg)
        except (TypeError, ValueError):
            return 0


@register.filter
def mul(value, arg):
    """Multiply the value by the arg."""
    try:
        return value * arg
    except TypeError:
        try:
            return float(value) * float(arg)
        except (TypeError, ValueError):
            return 0


@register.filter
def div(value, arg):
    """Divide the value by the arg."""
    try:
        return value / arg
    except (TypeError, ZeroDivisionError):
        try:
            return float(value) / float(arg)
        except (TypeError, ValueError, ZeroDivisionError):
            return 0

