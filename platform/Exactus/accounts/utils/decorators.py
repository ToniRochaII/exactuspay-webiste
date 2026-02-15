from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*allowed_roles):
    """
    Decorator that restricts access to users with specific roles.
    
    SAFE MODE:
    - Unauthorized users are always sent to 'dashboard'.
    - Prevents infinite redirect loops.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # 1. Authentication Check
            if not request.user.is_authenticated:
                return redirect("login")

            # 2. Normalize User Role
            user_role = getattr(request.user, "role", None)
            if user_role:
                user_role = user_role.upper()

            # 3. Normalize Allowed Roles
            allowed = {r.upper() for r in allowed_roles}

            # 4. Permission Check
            if user_role not in allowed:
                messages.error(request, "Access denied — insufficient permissions.")
                return redirect("dashboard")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def company_access_required(view_func):
    """
    Decorator that ensures the user is allowed to access the specific Company.
    
    LOGIC:
    - Checks kwargs for 'company_id' or 'pk'.
    - Global Roles (EXEC, ADMIN, COMPLIANCE) -> Access Granted.
    - Restricted Roles -> Must be explicitly linked to the company in 'user.contexts'.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        
        # 1. Identify the Company ID from the URL (kwargs)
        # Supports both 'company_id' (your custom PK) and standard 'pk'
        company_id = kwargs.get('company_id') or kwargs.get('pk')
        
        # If view doesn't use company_id, skip this specific check
        if not company_id:
            return view_func(request, *args, **kwargs)

        # 2. Define Global Roles (Bypass Check)
        global_roles = {"EXEC", "ADMIN", "COMPLIANCE"}
        user_role = getattr(request.user, "role", "").upper()

        if request.user.is_superuser or user_role in global_roles:
            return view_func(request, *args, **kwargs)

        # 3. Check Assignment (Contexts)
        # We filter the user's contexts to see if they are linked to this Company ID.
        has_access = request.user.contexts.filter(company_id=company_id).exists()

        if not has_access:
            messages.error(request, "Access Denied: You are not assigned to this company.")
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper