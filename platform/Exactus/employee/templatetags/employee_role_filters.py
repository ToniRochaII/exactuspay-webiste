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
def get_section(field):
    """Get the data-section attribute from a form field's widget"""
    return field.field.widget.attrs.get('data-section')

@register.filter
def in_section(field, section_name):
    """Check if a field belongs to a specific section"""
    return field.field.widget.attrs.get('data-section') == section_name

@register.simple_tag
def get_country_flag(country):
    """Returns flag emoji for country"""
    flags = {
        'brazil': '🇧🇷',
        'united-kingdom': '🇬🇧',
        'argentina': '🇦🇷',
    }
    return flags.get(country.slug, '🌐')