from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*allowed_roles):
    """
    Decorator that restricts access to users with specific roles.
    STRICT MODE: Superusers are NOT automatically granted access.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            
            # 1. Authentication Check
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this page.")
                return redirect("login")

            # 2. Normalize User Role
            user_role = getattr(request.user, "role", None)
            if user_role:
                user_role = user_role.upper()

            # 3. Normalize Allowed Roles
            normalized_allowed = {r.upper() for r in allowed_roles}

            # ---------------------------------------------------------
            # THE FIX: REMOVE OR COMMENT OUT THIS BLOCK
            # ---------------------------------------------------------
            # if getattr(request.user, "is_superuser", False):
            #     return view_func(request, *args, **kwargs)
            # ---------------------------------------------------------

            # 4. Permission Check
            if user_role not in normalized_allowed:
                messages.error(request, "Access denied — insufficient permissions.")
                return redirect("dashboard")

            # 5. Grant Access
            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator