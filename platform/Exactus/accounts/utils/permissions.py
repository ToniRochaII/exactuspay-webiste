from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache

from .access_control import AccessControl


def has_permission(user, domain, action):
    """
    Thin wrapper for backward compatibility and easy imports
    """
    return AccessControl.has_permission(user, domain, action)


def permission_required(domain, action, login_url=None):
    """
    Secure view decorator with proper permission checking.
    """
    def decorator(view_func):
        @wraps(view_func)
        @never_cache  # Prevent caching of permission-protected views
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect(login_url or "accounts:login")

            if not AccessControl.has_permission(request.user, domain, action):
                messages.error(request, "Access denied — insufficient permissions.")
                return redirect("accounts:dashboard")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def permission_required_any(permissions_list, login_url=None):
    """
    Decorator that requires ANY of the given permissions
    Usage: @permission_required_any([("USER", "READ"), ("REPORT", "EXPORT")])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to access this page.")
                return redirect(login_url or "accounts:login")

            # Check if user has any of the required permissions
            has_any = any(
                AccessControl.has_permission(request.user, domain, action)
                for domain, action in permissions_list
            )
            
            if not has_any:
                messages.error(request, "Access denied — insufficient permissions.")
                return redirect("accounts:dashboard")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator