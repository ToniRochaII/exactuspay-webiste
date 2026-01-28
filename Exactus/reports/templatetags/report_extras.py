from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Usage: {{ mydict|get_item:key }}
    Allows accessing dictionary values with a dynamic key in a template.
    """
    if dictionary:
        return dictionary.get(key)
    return None

# --- ADD THIS FUNCTION ---
@register.filter
def replace_underscore(value):
    """
    Usage: {{ value|replace_underscore }}
    Replaces underscores with spaces (e.g. 'first_name' -> 'first name').
    """
    if isinstance(value, str):
        return value.replace('_', ' ')
    return value