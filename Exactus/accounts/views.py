from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse

from collections import defaultdict
import csv
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model, logout, authenticate, login, views as auth_views

from django.db import transaction
from django.db.models import Q

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
    UserProfile,
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
    if request.user.role not in {"EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER"}:
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
    
    return render(request, 'login.html')

@login_required
def profile(request):
    """User's own profile - now uses unified template"""
    return unified_profile(request, user_id=None)


# Exactus/accounts/views.py
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Count, Max
from django.core.cache import cache
from Exactus.country.models import Country
from Exactus.company.models import Company
from Exactus.employee.models import Employee
from Exactus.payregister.models import PayRegister
from .models import UserPermissionHelper, Notification, UserCompany
from django.core.cache import cache

@login_required
def dashboard(request):
    """Regular user dashboard with real multi-tenant data"""
    
    cache_key = f'dashboard_{request.user.id}_{timezone.now().strftime("%Y%m%d")}'
    cached_data = cache.get(cache_key)
    
    if cached_data and not request.GET.get('refresh'):
        return render(request, 'dashboard/index.html', cached_data)
    
    now = timezone.now()
    
    # Get user's companies using helper
    user_companies = UserPermissionHelper.get_user_companies(request.user)
    user_companies_count = user_companies.count()
    
    # Get employees for user's companies
    if user_companies_count > 0:
        company_ids = user_companies.values_list('id', flat=True)
        from Exactus.employee.models import Employee
        user_employees_count = Employee.objects.filter(
            company_id__in=company_ids
        ).count()
        
        # Get recent payslips
        from Exactus.payregister.models import PayRegister
        recent_payslips = (
            PayRegister.objects
            .filter(employee__company_id__in=company_ids)
            .select_related('employee', 'employee__company')
            .order_by('-created_at')[:8]
        )
    else:
        user_employees_count = 0
        recent_payslips = []
    
    # Get real notifications
    notifications = Notification.objects.filter(
        user=request.user,
        archived=False
    ).order_by('-created_at')[:10]
    
    # Get pending approvals (notifications of type APPROVAL)
    pending_approvals_count = Notification.objects.filter(
        user=request.user,
        notification_type='APPROVAL',
        read=False,
        archived=False
    ).count()
    
    # Platform stats (cached)
    platform_stats_key = f'platform_stats_{now.strftime("%Y%m%d")}'
    platform_stats = cache.get(platform_stats_key)
    
    if not platform_stats:
        from Exactus.country.models import Country
        from Exactus.company.models import Company
        from Exactus.employee.models import Employee
        from Exactus.payregister.models import PayRegister
        
        platform_stats = {
            'active_countries_count': Country.objects.filter(status='ACTIVE').count(),
            'active_companies_count': Company.objects.filter(account_status='ACTIVE').count(),
            'total_employees_count': Employee.objects.count(),
            'payslips_30d_count': PayRegister.objects.filter(
                created_at__gte=now - timedelta(days=30)
            ).count(),
        }
        cache.set(platform_stats_key, platform_stats, 3600)
    
    # Get current month payroll runs for user's companies
    if user_companies_count > 0:
        from Exactus.payroll.models import Payroll
        current_month_payrolls_count = Payroll.objects.filter(
            company_id__in=company_ids,
            created_at__month=now.month,
            created_at__year=now.year
        ).count()
    else:
        current_month_payrolls_count = 0
    
    # Upcoming deadlines (example - in production, calculate from payroll schedules)
    upcoming_deadlines = []
    # TODO: Implement actual deadline calculation based on payroll schedules
    
    context = {
        # User-specific data
        'user_companies_count': user_companies_count,
        'user_employees_count': user_employees_count,
        'current_month_payrolls_count': current_month_payrolls_count,
        'pending_approvals_count': pending_approvals_count,
        
        # Platform stats
        'active_countries_count': platform_stats['active_countries_count'],
        'active_companies_count': platform_stats['active_companies_count'],
        'total_employees_count': platform_stats['total_employees_count'],
        'payslips_30d_count': platform_stats['payslips_30d_count'],
        
        # Activity feeds
        'recent_payslips': recent_payslips,
        'notifications': notifications,
        'upcoming_deadlines': upcoming_deadlines,
        
        # User info
        'user_role': request.user.get_role_display(),
        'cache_timestamp': now.isoformat(),
        
        # Companies list for quick access
        'user_companies': user_companies[:5],  # Show first 5
    }
    
    # Cache for 15 minutes
    cache.set(cache_key, context, 900)
    
    return render(request, 'dashboard/index.html', context)


# Exactus/accounts/views.py
from datetime import timedelta
import json
from django.utils import timezone
from django.db.models import Count, Q, F, Subquery, OuterRef
from django.db.models.functions import TruncMonth, Coalesce
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.cache import cache
from django.db import connection
from Exactus.country.models import Country
from Exactus.company.models import Company
from Exactus.employee.models import Employee
from Exactus.payregister.models import PayRegister
from Exactus.payroll.models import Payroll

def get_payroll_frequency_choices():
    """Safely get payroll frequency choices from model"""
    try:
        from Exactus.payroll.models import PAYROLL_FREQUENCY_CHOICES
        return PAYROLL_FREQUENCY_CHOICES
    except ImportError:
        # Fallback: get choices from the field definition
        field = Payroll._meta.get_field('payroll_frequency')
        return field.choices if hasattr(field, 'choices') else []

@login_required
def dashboard_admin(request):
    """Admin/Executive dashboard with platform analytics and caching"""
    
    # Check if user has admin/exec permissions
    if not hasattr(request.user, 'role') or request.user.role not in ['EXEC', 'ADMIN']:
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect('dashboard')
    
    # Generate cache key based on user and current month
    cache_key = f'dashboard_admin_{request.user.id}_{timezone.now().strftime("%Y%m")}'
    cached_data = cache.get(cache_key)
    
    if cached_data and not request.GET.get('refresh'):
        return render(request, 'dashboard/admin.html', cached_data)
    
    now = timezone.now()
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)
    
    # ──────────────── KPIs (Optimized Queries) ────────────────
    
    # Country metrics - single query with aggregation
    country_stats = Country.objects.aggregate(
        active_countries=Count('id', filter=Q(status='ACTIVE')),
        implementing_countries=Count('id', filter=Q(status='IMPLEMENTING')),
        inactive_countries=Count('id', filter=Q(status='INACTIVE')),
        total_countries=Count('id')
    )
    
    # Company metrics - single query
    company_stats = Company.objects.aggregate(
        active_companies=Count('id', filter=Q(account_status='ACTIVE')),
        suspended_companies=Count('id', filter=Q(account_status='SUSPENDED')),
        inactive_companies=Count('id', filter=Q(account_status='INACTIVE')),
        total_companies=Count('id')
    )
    
    # Employee metric - cached separately if large
    total_employees = cache.get('total_employees')
    if total_employees is None:
        total_employees = Employee.objects.count()
        cache.set('total_employees', total_employees, 3600)  # 1 hour cache
    
    # Payroll metrics
    total_payrolls = Payroll.objects.count()
    
    # Get payroll frequency choices safely
    payroll_choices = get_payroll_frequency_choices()
    monthly_patterns = ['monthly', 'semi-monthly', 'bi-weekly', 'biweekly']
    
    if payroll_choices:
        monthly_codes = [
            code for code, _ in payroll_choices 
            if any(pattern in code.lower().replace('_', '-') for pattern in monthly_patterns)
        ]
        monthly_payrolls = Payroll.objects.filter(payroll_frequency__in=monthly_codes).count()
    else:
        # Fallback to string matching
        monthly_payrolls = Payroll.objects.filter(
            Q(payroll_frequency__icontains='month') |
            Q(payroll_frequency__icontains='bi') |
            Q(payroll_frequency__icontains='semi')
        ).count()
    
    # Payslip metrics with optimized queries
    payslip_stats = {
        'payslips_total': PayRegister.objects.count(),
        'payslips_this_month': PayRegister.objects.filter(
            created_at__gte=start_of_month
        ).count(),
        'payslips_last_30d': PayRegister.objects.filter(
            created_at__gte=thirty_days_ago
        ).count(),
        'payslips_ytd': PayRegister.objects.filter(
            created_at__gte=start_of_year
        ).count(),
    }
    
    # Unique employees processed
    unique_employees_processed_total = cache.get('unique_employees_processed')
    if unique_employees_processed_total is None:
        unique_employees_processed_total = PayRegister.objects.values('employee').distinct().count()
        cache.set('unique_employees_processed', unique_employees_processed_total, 1800)  # 30 min cache
    
    # ──────────────── Charts Data (Optimized) ────────────────
    
    # Monthly payslips for last 12 months - using raw SQL for performance
    one_year_ago = now - timedelta(days=365)
    
    # Using Django's ORM for compatibility
    payslips_monthly = (
        PayRegister.objects.filter(created_at__gte=one_year_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    month_labels = []
    month_values = []
    for entry in payslips_monthly:
        month_labels.append(entry['month'].strftime('%b %Y'))
        month_values.append(entry['count'])
    
    # Payroll by frequency with fallback
    if payroll_choices:
        frequency_data = {}
        for code, name in payroll_choices:
            count = Payroll.objects.filter(payroll_frequency=code).count()
            if count > 0:
                display_name = name or code.replace('-', ' ').title()
                frequency_data[display_name] = count
        
        frequency_labels = list(frequency_data.keys())
        frequency_values = list(frequency_data.values())
    else:
        # Fallback: group by existing values
        payroll_counts = (
            Payroll.objects.values('payroll_frequency')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        frequency_labels = [item['payroll_frequency'].replace('-', ' ').title() 
                           for item in payroll_counts]
        frequency_values = [item['count'] for item in payroll_counts]
    
    # ──────────────── Map Data ────────────────
    
    # Active country codes with null check
    active_country_codes = list(
        Country.objects.filter(status='ACTIVE')
        .exclude(iso2_code__isnull=True)
        .exclude(iso2_code='')
        .values_list('iso2_code', flat=True)
    )
    
    # Get payslip counts per country with country filter
    payslips_by_country = (
        PayRegister.objects.filter(
            created_at__gte=start_of_year,
            employee__company__country__iso2_code__isnull=False
        )
        .values('employee__company__country__iso2_code')
        .annotate(
            count=Count('id'),
            country_name=F('employee__company__country__name')
        )
        .order_by('-count')
    )
    
    map_country_data = []
    for item in payslips_by_country:
        iso_code = item['employee__company__country__iso2_code']
        if iso_code:
            map_country_data.append({
                'code': iso_code.upper(),
                'name': item.get('country_name', 'Unknown'),
                'value': item['count']
            })
    
    # ──────────────── Top Companies (Optimized with Subquery) ────────────────
    
    # Get company IDs with most payslips first
    top_company_ids = (
        PayRegister.objects.filter(created_at__gte=start_of_year)
        .values('employee__company')
        .annotate(payslips_ytd=Count('id'))
        .order_by('-payslips_ytd')
        .values_list('employee__company', flat=True)[:10]
    )
    
    # Get company details in a single query
    from django.db.models import Subquery, OuterRef
    top_companies_qs = Company.objects.filter(id__in=top_company_ids)
    
    # Annotate with additional data
    top_companies = []
    for company in top_companies_qs:
        payslips_ytd = PayRegister.objects.filter(
            employee__company=company,
            created_at__gte=start_of_year
        ).count()
        
        total_employees = company.employees.count()
        
        top_companies.append({
            'id': company.id,
            'trade_name': company.trade_name or 'N/A',
            'country_name': company.country.name if company.country else 'N/A',
            'account_status': company.account_status,
            'payslips_ytd': payslips_ytd,
            'total_employees': total_employees
        })
    
    # Sort by payslips_ytd to maintain order
    top_companies.sort(key=lambda x: x['payslips_ytd'], reverse=True)
    
    # ──────────────── Recent Activity ────────────────
    
    # Optimized with select_related and prefetch_related
    recent_payslips = (
        PayRegister.objects
        .select_related('employee', 'employee__company', 'employee__company__country')
        .only(
            'created_at', 'amount', 'category',
            'employee__first_name', 'employee__last_name', 'employee__employee_id',
            'employee__company__trade_name',
            'employee__company__country__name'
        )
        .order_by('-created_at')[:10]
    )
    
    # Prepare context
    context = {
        # KPIs
        'active_countries': country_stats['active_countries'],
        'implementing_countries': country_stats['implementing_countries'],
        'inactive_countries': country_stats['inactive_countries'],
        'total_countries': country_stats['total_countries'],
        
        'active_companies': company_stats['active_companies'],
        'suspended_companies': company_stats['suspended_companies'],
        'inactive_companies': company_stats['inactive_companies'],
        'total_companies': company_stats['total_companies'],
        
        'total_employees': total_employees,
        'total_payrolls': total_payrolls,
        'monthly_payrolls': monthly_payrolls,
        
        # Payslip counts
        'payslips_total': payslip_stats['payslips_total'],
        'unique_employees_processed_total': unique_employees_processed_total,
        'payslips_this_month': payslip_stats['payslips_this_month'],
        'payslips_last_30d': payslip_stats['payslips_last_30d'],
        'payslips_ytd': payslip_stats['payslips_ytd'],
        
        # Chart Data
        'month_labels_json': json.dumps(month_labels),
        'month_values_json': json.dumps(month_values),
        'frequency_labels_json': json.dumps(frequency_labels),
        'frequency_values_json': json.dumps(frequency_values),
        
        # Map Data
        'active_country_codes_json': json.dumps(active_country_codes),
        'map_country_data_json': json.dumps(map_country_data),
        
        # Tables
        'top_companies': top_companies,
        'recent_payslips': recent_payslips,
        
        # Other
        'current_year': now.year,
        'cache_timestamp': now.isoformat(),
    }
    
    # Cache the entire context for 5 minutes
    cache.set(cache_key, context, 300)
    
    return render(request, 'dashboard/admin.html', context)

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
    if request.user.role not in ["EXEC","ADMIN","BILLING","IMPLEMENTATION","OPERATION", "DIRECTOR","MANAGER"]:
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
    """User detail view - now uses unified template"""
    return unified_profile(request, user_id=user_id)

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

@login_required
def unified_profile(request, user_id=None):
    """
    Debugging version to identify exactly where the issue is
    """
    print("=== PROFILE VIEW DEBUG ===")
    print(f"Method: {request.method}")
    print(f"User: {request.user}")
    print(f"user_id param: {user_id}")

    # Determine target user
    if user_id:
        target_user = get_object_or_404(User, id=user_id)
    else:
        target_user = request.user

    profile, created = UserProfile.objects.get_or_create(user=target_user)
    print(f"Profile: {profile}, Created: {created}")
    print(f"Current avatar: {profile.avatar}")

    is_own_profile = (request.user == target_user)
    can_edit = is_own_profile or AccessControl.has_permission(request.user, "USER", "UPDATE")

    # Initialize forms
    user_form = None
    profile_form = UserProfileForm(instance=profile)
    
    if not is_own_profile:
        user_form = UserEditForm(instance=target_user)

    # ==========================
    # POST HANDLING - DEBUG
    # ==========================
    if request.method == "POST":
        print(f"POST data: {dict(request.POST)}")
        print(f"FILES data: {dict(request.FILES)}")
        form_type = request.POST.get("form_type")
        print(f"Form type: {form_type}")

        if form_type == "profile":
            print("Processing PROFILE form")
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            print(f"Profile form valid: {profile_form.is_valid()}")
            print(f"Profile form errors: {profile_form.errors}")
            
            if profile_form.is_valid():
                saved_profile = profile_form.save()
                print(f"Saved profile avatar: {saved_profile.avatar}")
                messages.success(request, "Profile updated successfully.")
                return redirect(request.path)
            else:
                messages.error(request, f"Profile errors: {profile_form.errors}")

        elif form_type == "personal":
            print("Processing PERSONAL form")
            personal_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            print(f"Personal form valid: {personal_form.is_valid()}")
            print(f"Personal form errors: {personal_form.errors}")
            
            if personal_form.is_valid():
                saved_profile = personal_form.save()
                print(f"Saved personal info - avatar: {saved_profile.avatar}")
                messages.success(request, "Personal information updated.")
                return redirect(request.path)
            else:
                messages.error(request, f"Personal info errors: {personal_form.errors}")

        elif form_type == "notifications" and is_own_profile:
            print("Processing NOTIFICATIONS form")
            profile.notify_by_email = 'notify_by_email' in request.POST
            profile.notify_by_sms = 'notify_by_sms' in request.POST
            profile.save()
            messages.success(request, "Notification preferences updated.")
            return redirect(request.path)

    # ==========================
    # RENDER
    # ==========================
    context = {
        "target_user": target_user,
        "profile": profile,
        "form": user_form or profile_form,
        "profile_form": profile_form,
        "is_own_profile": is_own_profile,
        "can_edit": can_edit,
    }
    return render(request, "profile/unified_profile.html", context)


def get_safety_warnings(matrix):
    warnings = []
    
    # Finance must be read-only for payroll
    payroll_domains = ['PAYRUN', 'PAYREGISTER', 'CALCULATION', 'COMPANY', 'EMPLOYEE']
    for domain in payroll_domains:
        if matrix.get('FINANCE', {}).get(domain, {}).get('CREATE'):
            warnings.append(f"FINANCE has CREATE access to {domain} - violates read-only policy")
        if matrix.get('FINANCE', {}).get(domain, {}).get('DELETE'):
            warnings.append(f"FINANCE has DELETE access to {domain} - violates read-only policy")
    
    # Exec must have full system access
    if not matrix.get('EXEC', {}).get('USER', {}).get('MANAGE'):
        warnings.append("EXEC missing USER.MANAGE permission - system administration compromised")
    
    return warnings


# accounts/views.py
from django.views.decorators.cache import cache_page
from Exactus.accounts.services.permission_resolver import permission_resolver
from Exactus.accounts.services.conflict_detector import PermissionConflictDetector

@cache_page(60)  # Cache entire page for 1 minute
def role_management_view(request):
    """Enhanced role management view with caching and conflict detection"""
    
    # Resolve permissions using service layer
    effective_permissions = permission_resolver.resolve_permissions()
    
    # Detect permission conflicts in real-time
    conflict_detector = PermissionConflictDetector(effective_permissions)
    safety_warnings = conflict_detector.detect_conflicts()
    operational_risks = conflict_detector.detect_operational_risks()
    
    context = {
        'effective_permissions': effective_permissions,
        'safety_warnings': safety_warnings,
        'operational_risks': operational_risks,
        'conflict_summary': conflict_detector.get_conflict_summary(),
        # ... rest of your existing context
    }
    
    return render(request, 'role_management.html', context)

def compute_effective_permissions(matrix, hierarchy, protected_rules):
    """Compute final resolved permissions after all rules"""
    effective = {}
    
    for role in matrix.keys():
        effective[role] = {}
        
        # 1. Start with explicit permissions
        for domain, actions in matrix[role].items():
            effective[role][domain] = actions.copy()
        
        # 2. Apply hierarchy inheritance
        parent_role = hierarchy.get(role)
        if parent_role and parent_role in matrix:
            for domain, actions in matrix[parent_role].items():
                if domain not in effective[role]:
                    effective[role][domain] = {}
                for action, allowed in actions.items():
                    if allowed and not effective[role][domain].get(action):
                        effective[role][domain][action] = True
        
        # 3. Apply business logic protections
        apply_business_logic_protections(effective[role], role)
    
    return effective

def apply_business_logic_protections(permissions, role):
    """Apply ExactusPay-specific business logic rules"""
    payroll_domains = ['PAYRUN', 'PAYREGISTER', 'CALCULATION', 'COMPANY', 'EMPLOYEE', 'PDCODES']
    
    if role == 'FINANCE':
        # FINANCE is read-only for payroll operations
        for domain in payroll_domains:
            if domain in permissions:
                for action in ['CREATE', 'DELETE', 'UPDATE']:
                    permissions[domain][action] = False
    
    elif role in ['EXEC', 'ADMIN']:
        # EXEC/ADMIN must have full system access
        system_domains = ['USER', 'ROLE', 'SYSTEM']
        for domain in system_domains:
            if domain in permissions:
                permissions[domain]['MANAGE'] = True
                permissions[domain]['READ'] = True


