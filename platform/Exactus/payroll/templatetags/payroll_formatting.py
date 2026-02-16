
# Exactus/payroll/templatetags/payroll_formatting.py
from django import template
from django.utils import timezone
from datetime import datetime, date

register = template.Library()


# ------------------------------
# Number Formatting
# ------------------------------

@register.filter
def intcomma(value):
    """
    Converts a number into a string using commas.
    Example: 10000 -> "10,000"
    """
    try:
        value = float(value)
        return f"{value:,.0f}"
    except (ValueError, TypeError):
        return value


@register.filter
def floatcomma(value, decimals=2):
    """
    Format float with comma and specific decimals.
    Example: 12345.678 -> "12,345.68"
    """
    try:
        value = float(value)
        return f"{value:,.{decimals}f}"
    except (ValueError, TypeError):
        return value


@register.filter
def currency(value, symbol="£"):
    """
    Formats a number as currency.
    Example: 1500 -> "£1,500.00"
    """
    try:
        value = float(value)
        return f"{symbol}{value:,.2f}"
    except (ValueError, TypeError):
        return value


@register.filter
def percent(value, decimals=2):
    """
    Converts a decimal to a percentage string.
    Example: 0.25 -> "25%"
    """
    try:
        value = float(value) * 100
        return f"{value:.{decimals}f}%"
    except (ValueError, TypeError):
        return value


# ------------------------------
# Date / Time Formatting
# ------------------------------

@register.filter
def naturaldatetime(value):
    """
    Returns a human readable datetime format.
    Example: 2025-01-01 12:30 → "Jan 1, 2025 — 12:30"
    """
    if not isinstance(value, datetime):
        return value

    return value.strftime("%b %d, %Y — %H:%M")


@register.filter
def naturaldatetime_short(value):
    """
    Short form for datetime.
    Example: 2025-01-01 12:30 → "1 Jan 12:30"
    """
    if not isinstance(value, datetime):
        return value

    return value.strftime("%-d %b %H:%M")


@register.filter
def naturaldays(value):
    """
    Converts a date to a readable form.
    Example: 2025-01-01 → "Jan 1, 2025"
    """
    if not isinstance(value, (datetime, date)):
        return value

    return value.strftime("%b %-d, %Y")


# ------------------------------
# Duration Formatting
# ------------------------------

@register.filter
def seconds_to_hms(seconds):
    """
    Converts a number of seconds to HH:MM:SS.
    Example: 3661 → "01:01:01"
    """
    try:
        seconds = int(seconds)
    except (ValueError, TypeError):
        return seconds

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02}:{minutes:02}:{secs:02}"


# ------------------------------
# Payroll-specific formatting
# ------------------------------

@register.filter
def fy(value):
    """
    Converts a fiscal year number to display form.
    Example: 2025 -> "FY2025"
    """
    return f"FY{value}"


@register.filter
def status_badge(status):
    """
    Returns a Bootstrap badge class for statuses.
    Perfect for payroll + payroll periods.

    Use in template:
    <span class="badge {{ payroll.status|status_badge }}">{{ payroll.get_status_display }}</span>
    """
    mapping = {
        "draft": "bg-secondary",
        "open": "bg-primary",
        "processing": "bg-warning text-dark",
        "completed": "bg-success",
        "cancelled": "bg-danger",
    }
    return mapping.get(str(status).lower(), "bg-light text-dark")
