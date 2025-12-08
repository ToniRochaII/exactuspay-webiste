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


@register.filter
def add_class(field, css_class):
    """Add CSS class to form field widget."""
    if not field:
        return ""
    return field.as_widget(attrs={**field.field.widget.attrs, "class": css_class})


@register.filter
def is_tax_field(bound_field):
    """Return True if the bound field name starts with 'tax_id_'."""
    try:
        return bound_field.name.startswith("tax_id_")
    except Exception:
        return False