from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            # 1. Allow superusers always
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            # 2. Check if user has a role
            if not hasattr(user, "role") or not user.role:
                messages.error(request, "Access denied — insufficient permissions.")
                return redirect("country:country") # or your preferred landing page

            # 3. Normalize role to uppercase for matching
            user_role = user.role.upper()
            allowed_roles = [r.upper() for r in roles]

            if user_role not in allowed_roles:
                messages.error(request, "Access denied — insufficient permissions.")
                return redirect("country:country")

            # 4. User allowed
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
