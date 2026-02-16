from django import template

register = template.Library()

@register.filter(name="get_permission")
def get_permission(data, key):
    """
    Safely get nested permission data.
    Usage: permissions|get_permission:role|get_permission:domain|get_permission:action
    """
    try:
        if isinstance(data, dict):
            return data.get(key, {})
        return {}
    except (AttributeError, KeyError):
        return {}

@register.filter(name="dict_key")
def dict_key(dictionary, key):
    """Get a value from a dictionary by key."""
    try:
        return dictionary.get(key, 0)
    except (AttributeError, KeyError):
        return 0

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
