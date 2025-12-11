# Exactus/payroll/templatetags/payroll_filters.py
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
def completed_count(queryset):
    """Count completed periods in a queryset"""
    return queryset.filter(status='completed').count()

@register.filter
def total_amount(queryset):
    """Sum total_amount field in a queryset"""
    total = sum(float(item.total_amount) for item in queryset if item.total_amount)
    return total

@register.filter
def format_currency(value):
    """Format currency with thousands separator"""
    if value is None:
        return "0.00"
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return str(value)
    

@register.filter
def completed_count(queryset):
    """Count completed periods in a queryset"""
    return queryset.filter(status='COMPLETED').count()

@register.filter
def completed_percentage(queryset):
    """Calculate percentage of completed periods"""
    total = queryset.count()
    if total == 0:
        return 0
    completed = queryset.filter(status='COMPLETED').count()
    return (completed / total) * 100

# payroll/templatetags/payroll_filters.py
from django import template
from django.db.models import Sum, Count, Q
from django.contrib.humanize.templatetags.humanize import intcomma as django_intcomma

register = template.Library()

@register.filter
def completed_count(queryset):
    """Count completed periods in a queryset"""
    if hasattr(queryset, 'filter'):
        return queryset.filter(status='COMPLETED').count()
    return 0

@register.filter
def inprogress_count(queryset):
    """Count in-progress periods in a queryset"""
    if hasattr(queryset, 'filter'):
        return queryset.filter(status='PROCESSING').count()
    return 0

@register.filter
def total_amount(queryset):
    """Calculate total amount from a queryset of periods"""
    if hasattr(queryset, 'aggregate'):
        result = queryset.aggregate(total=Sum('total_amount'))
        return result['total'] or 0
    return 0

@register.filter
def intcomma(value, use_l10n=True):
    """Wrapper for Django's intcomma filter to avoid loading humanize in every template"""
    if value is None:
        return ''
    return django_intcomma(value, use_l10n)

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    if total == 0:
        return 0
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def status_badge_class(status):
    """Return appropriate Bootstrap badge class for status"""
    status_map = {
        'DRAFT': 'bg-warning',
        'PROCESSING': 'bg-info',
        'COMPLETED': 'bg-success',
        'PAID': 'bg-primary',
        'CANCELLED': 'bg-danger',
    }
    return status_map.get(status, 'bg-secondary')

@register.filter
def payroll_status_badge_class(status):
    """
    Returns a Bootstrap badge class for a given payroll status.

    Used in templates like:
      {{ payroll.status|payroll_status_badge_class }}

    Adjust the keys to match your PayrollStatus values
    (e.g. 'DRAFT', 'OPEN', 'COMPLETED', 'CANCELLED', etc).
    """
    if status is None:
        return "bg-secondary"

    key = str(status).lower()

    mapping = {
        "draft": "bg-secondary",
        "open": "bg-primary",
        "processing": "bg-warning text-dark",
        "completed": "bg-success",
        "closed": "bg-success",
        "cancelled": "bg-danger",
        "canceled": "bg-danger",
    }

    return mapping.get(key, "bg-light text-dark")
