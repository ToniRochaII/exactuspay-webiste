# accounts/templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    """Safely get a dictionary key in templates."""
    if isinstance(d, dict):
        return d.get(key)
    return None


