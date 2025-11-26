from Exactus.accounts.models import PermissionMatrix
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from Exactus.accounts.models import AccessControl

def has_permission(user, domain, action):
    if not user.is_authenticated:
        return False
    if getattr(user, "role", "").upper() == "ADMIN":
        return True
    role = getattr(user, "role", "").upper()
    return PermissionMatrix.objects.filter(
        role=role,
        domain__in=["ALL", domain],
        action__in=["ALL", action],
        allowed=True
    ).exists()

def permission_required(domain, action):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("login")

            # Superadmin override
            if request.user.role in ["EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE"]:
                return view_func(request, *args, **kwargs)

            # Check Permission Matrix
            if not AccessControl.has_permission(request.user, domain, action):
                messages.error(request, "Access denied — insufficient permissions.")
                return redirect("dashboard")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator