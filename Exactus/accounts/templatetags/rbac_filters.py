from django import template

register = template.Library()

@register.filter
def calculate_permission_count(effective_perms, actions):
    """Calculate total number of granted permissions"""
    count = 0
    for domain, perms in effective_perms.items():
        for action in actions:
            if perms.get(action):
                count += 1
    return count

@register.filter
def calculate_manage_permissions(effective_perms):
    """Calculate number of MANAGE permissions"""
    count = 0
    for domain, perms in effective_perms.items():
        if perms.get('MANAGE'):
            count += 1
    return count

@register.filter
def calculate_payroll_permissions(effective_perms, payroll_domains):
    """Calculate payroll-related permissions"""
    count = 0
    for domain in payroll_domains:
        if domain in effective_perms:
            for action, allowed in effective_perms[domain].items():
                if allowed:
                    count += 1
    return count

@register.filter
def dict_get(value, arg):
    """Template filter to get dictionary value by key"""
    return value.get(arg) if value else None

@register.filter
def get_permission(value, key):
    """Get permission value from nested dict"""
    if isinstance(value, dict):
        return value.get(key, {})
    return {}

@register.filter
def dict_key(value, key):
    """Get value from dictionary by key"""
    if isinstance(value, dict):
        return value.get(key)
    return None