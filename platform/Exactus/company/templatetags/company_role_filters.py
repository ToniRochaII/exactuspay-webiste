from django import template
register = template.Library()

@register.filter
def has_role(user, roles):
    """Check if user's role is in a comma-separated list of roles."""
    if not user or not hasattr(user, "role"):
        return False
    role_list = [r.strip().upper() for r in roles.split(",")]
    return user.role.upper() in role_list


@register.filter
def contains(list_string, item):
    """
    Check if item is inside a space-separated string list.
    Usage: {% if field.name|contains:company_fields %}.
    """
    items = [x.strip() for x in str(list_string).split()]
    return item in items

@register.filter
def add_class(field, css_class):
    """Add CSS class to form field"""
    if field is None:
        return ""
    return field.as_widget(attrs={"class": css_class})

@register.filter
def get_field(form, field_name):
    """Get a field from a form by name"""
    try:
        return form[field_name]
    except KeyError:
        return None

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter"""
    return value.split(delimiter)