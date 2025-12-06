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
def get_bracket_field(form, index):
    """Get bracket field by index (00-15)"""
    field_name = f"bracket_{index:02d}"
    return form[field_name]

@register.filter
def get_bracket_field_id(form, index):
    """Get bracket field ID by index"""
    field_name = f"bracket_{index:02d}"
    return form[field_name].id_for_label

@register.filter
def get_rate_field(form, index):
    """Get rate field by index (00-15)"""
    field_name = f"rate_{index:02d}"
    return form[field_name]

@register.filter
def get_rate_field_id(form, index):
    """Get rate field ID by index"""
    field_name = f"rate_{index:02d}"
    return form[field_name].id_for_label