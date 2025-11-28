from collections import defaultdict
import csv
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, logout, authenticate, login, views as auth_views
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from Exactus.accounts.utils.access_control import AccessControl
from Exactus.accounts.utils.permissions import permission_required

from Exactus.accounts.forms import UserEditForm, UserRegistrationForm, LoginForm, UserProfileForm
from Exactus.accounts.models import (
    RoleHierarchy,
    User,
    PermissionMatrix,
    RoleTemplate,
)
from Exactus.accounts.utils.permissions import has_permission
from Exactus.accounts.utils.role_hierarchy import promote_role, demote_role


User = get_user_model()

def get_pending_regulation_updates():
    """
    Return the number of regulations that still require an update.
    Attempts to use a `regulations` app if it exists, otherwise defaults to 0
    so the dashboard continues to function even when the compliance app
    hasn't been installed yet.
    """
    candidates = ("RegulationUpdate", "Regulation")
    RegulationModel = None

    for model_name in candidates:
        try:
            RegulationModel = apps.get_model("regulations", model_name)
            break
        except LookupError:
            continue

    if RegulationModel is None:
        return 0

    field_names = {field.name for field in RegulationModel._meta.concrete_fields}
    qs = RegulationModel.objects.all()

    def filter_count(field_name, value, case_insensitive=False):
        lookup = f"{field_name}__iexact" if case_insensitive and isinstance(value, str) else field_name
        return qs.filter(**{lookup: value}).count()

    if "status" in field_names:
        pending_value = getattr(getattr(RegulationModel, "Status", None), "PENDING", None)
        if pending_value is not None:
            return filter_count("status", pending_value)
        return filter_count("status", "PENDING", case_insensitive=True)

    if "state" in field_names:
        pending_value = getattr(getattr(RegulationModel, "State", None), "PENDING", None)
        if pending_value is not None:
            return filter_count("state", pending_value)
        return filter_count("state", "PENDING", case_insensitive=True)

    if "is_pending" in field_names:
        return filter_count("is_pending", True)

    if "needs_update" in field_names:
        return filter_count("needs_update", True)

    if "requires_update" in field_names:
        return filter_count("requires_update", True)

    if "is_up_to_date" in field_names:
        return filter_count("is_up_to_date", False)

    return qs.count()


@login_required
def register(request):
    # Only admins can access this view
    if request.user.role not in {"EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE"}:
        messages.error(request, "Access denied: only administrators can create new users.")
        return redirect("dashboard")

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect("dashboard")  # or redirect('dashboard_admin') if that exists
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Handle "Remember me" functionality
            if not remember_me:
                # Session will expire when browser closes
                request.session.set_expiry(0)
            
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to next parameter or dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

@login_required
def profile(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'profile/index.html', {'form': form})

@login_required
def dashboard(request):
    if request.user.role not in {"EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION", "DIRECTOR","MANAGER","SPECIALIST","FINANCE","EMPLOYEE"}:
        messages.error(request, "Access denied.")
        return render(request, 'dashboard/index.html')

@login_required
def dashboard_admin(request):
    if request.user.role not in {"EXEC"}:
        messages.error(request, "Access denied.")
        return redirect('dashboard')  # or your generic dashboard

    # --- Metrics (replace with real queries as other apps land) ---
    now = timezone.now()
    last_30 = now - timedelta(days=30)

    total_users = User.objects.count()
    active_staff = User.objects.filter(is_staff=True).count()
    new_users_30d = User.objects.filter(date_joined__gte=last_30).count()

    # Example "compliance status” placeholder
    compliance_summary = {
        "countries_configured": 3,     # TODO: replace with countries.models.Country.objects.count()
        "pending_updates": get_pending_regulation_updates(),
        "status": "Amber",             # Green/Amber/Red based on rules
    }

    # Example "billing overview” placeholder
    billing_overview = {
        "mrr": 12500,                  # Monthly Recurring Revenue (£)
        "ar_overdue": 2300,            # Accounts receivable overdue (£)
        "invoices_this_month": 14,     # Count
    }

    # Example series for charts (stubbed—replace later)
    users_by_role = {
    "EXEC": User.objects.filter(role="EXEC").count(),
    "ADMIN": User.objects.filter(role="ADMIN").count(),
    "COMPLIANCE": User.objects.filter(role="COMPLIANCE").count(),
    "BILLING": User.objects.filter(role="BILLING").count(),
    "IMPLEMENTATION": User.objects.filter(role="IMPLEMENTATION").count(),
    "OPERATION": User.objects.filter(role="OPERATION").count(),
    "DIRECTOR": User.objects.filter(role="DIRECTOR").count(),
    "MANAGER": User.objects.filter(role="MANAGER").count(),
    "SPECIALIST": User.objects.filter(role="SPECIALIST").count(),
    "FINANCE": User.objects.filter(role="FINANCE").count(),
    "EMPLOYEE": User.objects.filter(role="EMPLOYEE").count(),
    }

    signups_last_7_days = []  # list of {"day": "2025-11-09", "count": 2}
    for i in range(7, 0, -1):
        day = now - timedelta(days=i)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        count = User.objects.filter(date_joined__range=(start, end)).count()
        signups_last_7_days.append({"day": start.strftime("%Y-%m-%d"), "count": count})

    context = {
        "total_users": total_users,
        "active_staff": active_staff,
        "new_users_30d": new_users_30d,
        "compliance_summary": compliance_summary,
        "billing_overview": billing_overview,
        "users_by_role": users_by_role,
        "signups_last_7_days": signups_last_7_days,
    }
    return render(request, "dashboard/admin.html", context)


class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
    success_url = reverse_lazy('auth/password_reset_done')

    def form_valid(self, form):
        messages.info(self.request, "If your email exists, you’ll receive reset instructions shortly.")
        return super().form_valid(form)

class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'auth/password_reset_done.html'

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'auth//password_reset_confirm.html'
    success_url = reverse_lazy('auth/password_reset_complete')

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully.")
        return super().form_valid(form)

class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'auth/password_reset_complete.html'





@login_required
def user_list(request):
    """Admin-only user list with filtering, search and bulk actions."""
    if request.user.role not in ["EXEC","ADMIN","BILLING","IMPLEMENTATION","OPERATION"]:
        return redirect("dashboard")

    users = User.objects.all()

    # --- Filtering ---
    role_filter = request.GET.get("role")
    search_query = request.GET.get("q")

    if role_filter and role_filter != "ALL":
        users = users.filter(role=role_filter)

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    # --- Bulk actions (optional future hook) ---
    if request.method == "POST":
        action = request.POST.get("action")
        selected = request.POST.getlist("selected_users")
        if action == "deactivate":
            User.objects.filter(id__in=selected).update(is_active=False)
            messages.success(request, f"{len(selected)} users deactivated.")
        elif action == "activate":
            User.objects.filter(id__in=selected).update(is_active=True)
            messages.success(request, f"{len(selected)} users activated.")
        elif action == "delete":
            User.objects.filter(id__in=selected).delete()
            messages.warning(request, f"{len(selected)} users deleted.")
        return redirect("user_list")

    context = {
        "users": users,
        "roles": User.ROLE_CHOICES,
        "role_filter": role_filter or "ALL",
        "search_query": search_query or "",
    }
    return render(request, "management/user_list.html", context)


@login_required
def export_users_csv(request):
    """Exports filtered users to CSV."""
    if request.user.role not in {"EXEC","ADMIN","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE"}:
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    users = User.objects.all()
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="users.csv"'

    writer = csv.writer(response)
    writer.writerow(["Username", "Email", "Role", "Active", "Joined"])

    for u in users:
        writer.writerow([u.username, u.email, u.role, u.is_active, u.date_joined])

    return response



@login_required
def user_detail(request, user_id):
    """View detailed information about a specific user."""
    if request.user.role not in {"EXEC","ADMIN","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE"}:
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)

    # Example data - replace with your actual relations later
    activity_log = [
        {"action": "Logged in", "timestamp": "2025-11-09 09:32"},
        {"action": "Edited profile", "timestamp": "2025-11-08 14:11"},
        {"action": "Viewed payroll report", "timestamp": "2025-11-07 10:44"},
    ]

    associated_companies = [
        {"name": "Exactus Global Ltd", "role": "Payroll Manager"},
        {"name": "ExactusPay France", "role": "Viewer"},
    ]

    context = {
        "user_obj": user,
        "activity_log": activity_log,
        "associated_companies": associated_companies,
    }
    return render(request, "management/user_detail.html", context)

@login_required
def user_edit(request, user_id):
    """Allow admin to edit user role, permissions, and status."""
    if request.user.role not in {"EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION"}:
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    user_obj = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user_obj.username}' updated successfully.")
            return redirect("user_detail", user_id=user_obj.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserEditForm(instance=user_obj)

    context = {"form": form, "user_obj": user_obj}
    return render(request, "management/user_edit.html", context)

@permission_required("ROLE", "READ")
def role_management(request):
    """
    Enhanced role management with effective permission display
    """
    roles = [r for r, _ in PermissionMatrix.ROLE_CHOICES]
    domains = [d for d, _ in PermissionMatrix.DOMAIN_CHOICES]
    actions = [a for a, _ in PermissionMatrix.ACTION_CHOICES]

    # Build permission matrix
    matrix = {
        r: {d: {a: False for a in actions} for d in domains}
        for r in roles
    }

    for row in PermissionMatrix.objects.all().only("role", "domain", "action", "allowed"):
        if row.role in matrix and row.domain in matrix[row.role]:
            matrix[row.role][row.domain][row.action] = row.allowed

    # Get effective permissions for each role (for UI display)
    effective_permissions = {}
    for role in roles:
        effective_permissions[role] = AccessControl.get_effective_permissions(role)

    context = {
        "roles": roles,
        "domains": domains,
        "actions": actions,
        "matrix": matrix,
        "effective_permissions": effective_permissions,  # NEW: Show expanded perms
        "templates": RoleTemplate.objects.all().order_by("name"),
        "users": User.objects.all().order_by("username"),
        "hierarchy": dict(RoleHierarchy.objects.values_list('parent', 'child')),
    }
    
    # ... rest of your existing role_management logic ...
    return render(request, "roles/role_management.html", context)