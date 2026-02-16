from django import template
from Exactus.accounts.utils.access_control import AccessControl

register = template.Library()

@register.filter(name='can')
def can(user, permission_string):
    """
    Usage in template: {% if user|can:"COMPANY:READ" %}
    """
    if not user or not user.is_authenticated:
        return False

    try:
        # Split "COMPANY:READ" into domain and action
        domain, action = permission_string.split(':')
        
        # Call the robust AccessControl engine
        return AccessControl.has_permission(user, domain, action)
    except ValueError:
        # Failsafe if string format is wrong
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