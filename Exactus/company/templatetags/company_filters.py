from django import template

register = template.Library()

@register.filter
def contains(list_string, item):
    """
    Check if item is inside a space-separated string list.
    Usage: {% if field.name|contains:company_fields %}.
    """
    items = [x.strip() for x in str(list_string).split()]
    return item in items
