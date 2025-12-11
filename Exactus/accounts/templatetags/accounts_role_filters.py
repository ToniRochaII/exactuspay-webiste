from django import template
register = template.Library()

@register.filter
def has_role(user, roles):
    """Check if user's role is in a comma-separated list of roles."""
    if not user or not hasattr(user, "role"):
        return False
    role_list = [r.strip().upper() for r in roles.split(",")]

    return user.role.upper() in role_list

@register.filter(name="dict_key")
def dict_key(dictionary, key):
    """
    Safely return dictionary[key] in templates.
    If key does not exist, return 0.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0

@register.filter(name="get_permission")
def get_permission(data, key):
    """
    Safely get nested permission data.
    Usage: permissions|get_permission:role|get_permission:domain|get_permission:action
    """
    try:
        return data.get(key, {}) if isinstance(data, dict) else {}
    except (AttributeError, KeyError):
        return {}
    

@register.filter
def can_manage_company(user, company):
    """
    Returns True if the user is allowed to manage the given company.
    Adjust this logic to match your real permission model.
    """
    if not user.is_authenticated:
        return False

    # Simple default logic – tweak as needed
    if user.is_superuser or user.is_staff:
        return True

    # If you have Django perms on the Company model
    if user.has_perm('company.change_company') or user.has_perm('company.view_company'):
        return True

    # If you later have a more advanced RBAC, replace with that check.
    return False
