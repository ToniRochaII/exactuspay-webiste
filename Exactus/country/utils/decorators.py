from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(*required_roles):
    """
    Checks if the user has ANY of the required roles.
    Checks BOTH Global User Role and Company Context Roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            user = request.user

            # --- 1. SUPERUSER / GLOBAL ADMIN BYPASS ---
            # If the user is a superuser or has a high-level global role, grant access immediately.
            # Adjust 'EXEC'/'ADMIN' to match the exact strings in your User.ROLE_CHOICES
            GLOBAL_ADMIN_ROLES = {'EXEC', 'ADMIN'}
            if user.is_superuser or user.role in GLOBAL_ADMIN_ROLES:
                return view_func(request, *args, **kwargs)

            # --- 2. GATHER ALL USER ROLES ---
            # Start with the user's global role (e.g., 'EMPLOYEE', 'MANAGER')
            current_roles = {user.role}

            # Add context-specific roles from the database (UserCompany table)
            # This handles the "context_roles" middleware optimization if you have it,
            # otherwise it queries the database.
            if hasattr(request, 'context_roles'):
                current_roles.update(request.context_roles)
            else:
                # Fallback: Query the DB using the correct related_name 'company_access'
                company_roles = user.company_access.values_list('role', flat=True)
                current_roles.update(company_roles)

            # --- 3. CHECK PERMISSION ---
            # Check if there is any overlap between User's roles and Required roles
            has_permission = bool(current_roles.intersection(required_roles))

            if has_permission:
                return view_func(request, *args, **kwargs)
            
            # --- 4. HANDLE DENIAL ---
            # Debugging: Print to console so you can see why it failed
            print(f"DEBUG: User Roles: {current_roles} | Required: {required_roles}")
            
            messages.error(request, "Access Denied: You do not have the required role for this area.")
            return redirect('dashboard')
            
        return _wrapped_view
    return decorator