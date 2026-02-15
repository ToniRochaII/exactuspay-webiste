from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get a value from a dictionary by key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def get_nested(dictionary, keys):
    """
    Usage: {{ matrix|get_nested:role|get_nested:domain|get_nested:action }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(keys)
    return None