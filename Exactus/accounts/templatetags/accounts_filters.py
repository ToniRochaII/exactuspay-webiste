from django import template

register = template.Library()

@register.filter(name="dict_key")
def dict_key(dictionary, key):
    """
    Safely return dictionary[key] in templates.
    If key does not exist, return 0.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0