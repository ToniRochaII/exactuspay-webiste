from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*allowed_roles):
    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("login")

            # Normalize both sides
            user_role = getattr(request.user, "role", None)
            if user_role:
                user_role = user_role.upper()
            allowed = [r.upper() for r in allowed_roles]

            if user_role not in allowed:
                messages.error(request, "Access denied — insufficient permissions.")

                country_slug = kwargs.get("country_slug")
                if country_slug:
                    return redirect("companies:company", country_slug=country_slug)

                return redirect("country:country")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
