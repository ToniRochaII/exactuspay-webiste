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


from django import forms

register = template.Library()

@register.filter
def add_class(field, css_class):
    """Add CSS class to form field widget"""
    if hasattr(field, 'field') and hasattr(field.field, 'widget'):
        attrs = field.field.widget.attrs.copy()
        attrs['class'] = attrs.get('class', '') + ' ' + css_class
        return field.as_widget(attrs=attrs)
    return field

@register.filter
def is_tax_field(field):
    return field.name.startswith('tax_id_')

@register.filter
def is_bank_field(field):
    return field.name.startswith('bank_')

@register.filter
def is_government_field(field):
    return field.name.startswith('government_id_')

@register.filter
def is_visible(field):
    """Check if field is not hidden"""
    return not isinstance(field.field.widget, forms.HiddenInput)

@register.filter
def get_field(form, field_name):
    """Get a field from a form by name"""
    return form.get(field_name, None)

@register.simple_tag
def is_field_visible(form, field_name):
    """Check if a specific field exists and is visible"""
    if field_name in form.fields:
        return not isinstance(form.fields[field_name].widget, forms.HiddenInput)
    return False

@register.simple_tag
def get_field_help_text(form, field_name):
    """Get help text for a field"""
    if field_name in form.fields:
        return form.fields[field_name].help_text
    return ''