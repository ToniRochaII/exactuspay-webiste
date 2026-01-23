# employee/templatetags/form_helpers.py
from django import template

register = template.Library()

@register.filter
def get_section(field):
    """Get the data-section attribute from a form field's widget"""
    return field.field.widget.attrs.get('data-section')

def in_section(field, section_name):
    """Check if a form field belongs to a specific section."""
    data_section = field.field.widget.attrs.get('data-section')
    return data_section == section_name
