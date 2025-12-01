from django import template

register = template.Library()

@register.filter(name="get_permission")
def get_permission(data, key):
    """
    Safely get nested permission data.
    Usage: permissions|get_permission:role|get_permission:domain|get_permission:action
    """
    try:
        if isinstance(data, dict):
            return data.get(key, {})
        return {}
    except (AttributeError, KeyError):
        return {}

@register.filter(name="dict_key")
def dict_key(dictionary, key):
    """Get a value from a dictionary by key."""
    try:
        return dictionary.get(key, 0)
    except (AttributeError, KeyError):
        return 0
