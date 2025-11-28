from django import template
from Exactus.accounts.utils.access_control import AccessControl

register = template.Library()


@register.filter
def can(user, permission_string):
    """Usage: {% if user|can:"USER:READ" %}"""
    try:
        domain, action = permission_string.split(":")
        return AccessControl.has_permission(user, domain.strip(), action.strip())
    except:
        return False


@register.simple_tag
def check_permission(user, domain, action):
    return AccessControl.has_permission(user, domain, action)
