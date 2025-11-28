from django import template
from Exactus.accounts.utils.access_control import AccessControl

register = template.Library()


@register.filter
def can(user, permission_string):
    """
    Check if user has permission: {{ user|can:"USER:READ" }}
    """
    try:
        domain, action = permission_string.split(":", 1)
        return AccessControl.has_permission(user, domain.strip(), action.strip())
    except (ValueError, AttributeError):
        return False


@register.simple_tag
def check_permission(user, domain, action):
    """
    Check permission with explicit domain/action
    {% check_permission user "USER" "READ" as can_read %}
    """
    return AccessControl.has_permission(user, domain, action)


@register.filter
def get_effective_permissions(role):
    """
    Get all effective permissions for a role (for admin displays)
    {{ "MANAGER"|get_effective_permissions }}
    """
    return AccessControl.get_effective_permissions(role)