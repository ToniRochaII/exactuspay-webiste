# employee/templatetags/form_helpers.py
from django import template

register = template.Library()

@register.filter
def get_section(field):
    """Get the data-section attribute from a form field's widget"""
    return field.field.widget.attrs.get('data-section')

@register.filter
def in_section(field, section_name):
    """Check if a field belongs to a specific section"""
    return field.field.widget.attrs.get('data-section') == section_name

