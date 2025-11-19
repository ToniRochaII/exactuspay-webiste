from django.contrib import messages
from django.shortcuts import redirect


def role_required(*roles):
    """
    Restricts access to users whose profile.role is in the given roles.
    Example:
        @role_required("ADMIN", "MANAGER")
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, "profile") or request.user.profile.role not in roles:
                messages.error(request, "Access denied — insufficient permissions.")
                return redirect("home")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
