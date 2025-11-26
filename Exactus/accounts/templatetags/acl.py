from django import template
from Exactus.accounts.utils.permissions import has_permission

register = template.Library()

@register.filter
def can(user, permission_string):
    try:
        domain, action = permission_string.split(':')
        return has_permission(user, domain, action)
    except:
        return False

@register.simple_tag
def check_permission(user, domain, action):
    return has_permission(user, domain, action)