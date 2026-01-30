import csv
import json
import time
import datetime
from datetime import timedelta
from collections import defaultdict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.apps import apps
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache

from django.contrib.auth import get_user_model, authenticate, login, logout as auth_logout, views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt

from django.db import transaction
from django.db.models import Q, Count, Sum, F
from django.db.models.functions import TruncMonth
from django.db.models import Count

# Internal Exactus Imports
from Exactus.company import admin
from Exactus.country.utils.decorators import role_required
from Exactus.accounts.utils.access_control import AccessControl
from Exactus.accounts.utils.permissions import permission_required, has_permission
from Exactus.accounts.utils.role_hierarchy import promote_role, demote_role
from Exactus.accounts.services.onboarding import OnboardingService
from Exactus.accounts.forms import UserEditForm, UserRegistrationForm, LoginForm, UserProfileForm
from Exactus.country.models import Country
from Exactus.company.models import Company  
from Exactus.accounts.models import (
    User,
    UserProfile,
    RoleHierarchy,
    PermissionMatrix,
    RoleTemplate,
)

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
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
def profile(request):
    """User's own profile - uses unified template."""
    return unified_profile(request, user_id=None)







class CustomPasswordResetView(auth_views.PasswordResetView):
    """Custom password reset view."""
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
    success_url = reverse_lazy('auth/password_reset_done')

    def form_valid(self, form):
        messages.info(self.request, "If your email exists, you'll receive reset instructions shortly.")
        return super().form_valid(form)


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    """Custom password reset done view."""
    template_name = 'auth/password_reset_done.html'


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Custom password reset confirm view."""
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('auth/password_reset_complete')

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully.")
        return super().form_valid(form)


class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """Custom password reset complete view."""
    template_name = 'auth/password_reset_complete.html'





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
    """User detail view - uses unified template."""
    return unified_profile(request, user_id=user_id)








@permission_required("ROLE", "READ")
def role_management(request):
    """Enhanced role management with effective permission display."""
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

    # Get effective permissions for each role
    effective_permissions = {}
    for role in roles:
        effective_permissions[role] = AccessControl.get_effective_permissions(role)

    context = {
        "roles": roles,
        "domains": domains,
        "actions": actions,
        "matrix": matrix,
        "effective_permissions": effective_permissions,
        "templates": RoleTemplate.objects.all().order_by("name"),
        "users": User.objects.all().order_by("username"),
        "hierarchy": dict(RoleHierarchy.objects.values_list('parent', 'child')),
    }
    
    return render(request, "roles/role_management.html", context)




def get_safety_warnings(matrix):
    """Generate safety warnings for permission matrix."""
    warnings = []
    
    # Finance must be read-only for payroll
    payroll_domains = ['PAYRUN',  'CALCULATION', 'COMPANY', 'EMPLOYEE']
    for domain in payroll_domains:
        if matrix.get('FINANCE', {}).get(domain, {}).get('CREATE'):
            warnings.append(f"FINANCE has CREATE access to {domain} - violates read-only policy")
        if matrix.get('FINANCE', {}).get(domain, {}).get('DELETE'):
            warnings.append(f"FINANCE has DELETE access to {domain} - violates read-only policy")
    
    # Exec must have full system access
    if not matrix.get('EXEC', {}).get('USER', {}).get('MANAGE'):
        warnings.append("EXEC missing USER.MANAGE permission - system administration compromised")
    
    return warnings


def compute_effective_permissions(matrix, hierarchy, protected_rules):
    """Compute final resolved permissions after all rules."""
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
    """Apply ExactusPay-specific business logic rules."""
    payroll_domains = ['PAYRUN',  'CALCULATION', 'COMPANY', 'EMPLOYEE', 'PDCODES']
    
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





@login_required
def admin_reset_password(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Prevent resetting own password from admin tools
    if user == request.user:
        messages.error(request, "You cannot reset your own password here.")
        return redirect("user_edit", id=user_id)

    token = default_token_generator.make_token(user)

    reset_url = request.build_absolute_uri(f"/reset/{user.pk}/{token}/")

    # Send email
    subject = "Password Reset Request"
    message = render_to_string("emails/admin_reset_password.html", {
        "user": user,
        "reset_url": reset_url,
    })

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False
    )

    messages.success(request, f"Password reset email sent to {user.email}")
    return redirect("user_edit", id=user_id)


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@require_POST
def tab_close_detection(request):
    """Handle tab close detection from beacon API"""
    if request.user.is_authenticated:
        # You could log this event or clean up session data
        print(f"User {request.user.username} closed tab")
    
    return JsonResponse({'status': 'ok'})


import time
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST







@login_required
@require_GET
def session_status(request):
    """Debug endpoint to check session status."""
    last_activity = request.session.get('last_activity', time.time())
    elapsed = time.time() - last_activity
    remaining = max(300 - elapsed, 0)
    
    return JsonResponse({
        'authenticated': True,
        'username': request.user.username,
        'remaining_seconds': int(remaining),
        'last_activity': last_activity,
        'percent_remaining': int((remaining / 300) * 100),
        'server_time': timezone.now().isoformat()
    })






# ──────────────────────────────────────────────────────────────────────────────
# 1. AUTHENTICATION & REGISTRATION
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def register(request):
    """Admin user creation triggering the Onboarding flow."""
    allowed_roles = {"EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER"}
    user_role = getattr(request.user, 'role', None)
    
    if user_role not in allowed_roles:
        messages.error(request, "Access denied: only administrators can create new users.")
        return redirect("dashboard")

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            try:
                OnboardingService.onboard_employee(
                    username=username,
                    email=email,
                    role=role,
                    created_by_user=request.user
                )
                messages.success(request, f"User '{username}' created. Credentials have been emailed.")
                return redirect("user_list") 
            except Exception as e:
                messages.error(request, f"Error creating user: {str(e)}")

    return render(request, 'auth/register.html', {'roles': User.ROLE_CHOICES})

def custom_login(request):
    """Custom login view with remember me functionality."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def enhanced_logout(request):
    """Custom logout that clears session data."""
    from django.contrib.auth import logout as auth_logout
    if request.user.is_authenticated:
        if 'last_activity' in request.session:
            del request.session['last_activity']
        auth_logout(request)
        messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

# ──────────────────────────────────────────────────────────────────────────────
# 2. DASHBOARDS
# ──────────────────────────────────────────────────────────────────────────────

import json
from datetime import timedelta, date
from django.utils import timezone
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.apps import apps

def get_dashboard_context(request):
    """
    Comprehensive executive dashboard context with Gross and Net totals.
    """
    Company = apps.get_model('company', 'Company')
    Employee = apps.get_model('employee', 'Employee')
    PayrollResult = apps.get_model('payroll', 'PayrollResult')
    Country = apps.get_model('country', 'Country')

    today = timezone.now().date()
    one_year_ago = today - timedelta(days=365)

    # 1. Base Queryset for the last 12 months
    results_qs = PayrollResult.objects.filter(
        period__payment_date__gte=one_year_ago
    ).select_related('period', 'period__payroll__company__country')

    # 2. Financial Aggregation
    # Note: Replace 'gross_pay' and 'net_pay' with your actual model field names
    totals = results_qs.aggregate(
        total_gross=Sum('gross_pay'), # This specifically maps to Code 5000 logic
        total_net=Sum('net_pay'),
        total_count=Count('id')
    )

    total_payslips = totals['total_count'] or 0
    total_gross_amount = totals['total_gross'] or 0
    total_net_amount = totals['total_net'] or 0

    # 3. Monthly Financial Trends
    monthly_stats = (
        results_qs.annotate(month=TruncMonth('period__payment_date'))
        .values('month')
        .annotate(
            payslip_count=Count('id'),
            monthly_gross=Sum('gross_pay'),
            monthly_net=Sum('net_pay')
        )
        .order_by('month')
    )

    bar_labels = [s['month'].strftime('%b %Y') for s in monthly_stats]
    payslip_trend_data = [s['payslip_count'] for s in monthly_stats]
    gross_value_trend = [float(s['monthly_gross'] or 0) for s in monthly_stats]
    net_value_trend = [float(s['monthly_net'] or 0) for s in monthly_stats]

    # 4. KPI Counts
    active_companies_qs = Company.objects.filter(account_status='ACTIVE')
    active_headcount = Employee.objects.filter(
        Q(employment_end_date__isnull=True) | Q(employment_end_date__gt=today)
    ).count()

    # 5. Top Countries
    top_countries = list(
        Country.objects.filter(companies__account_status='ACTIVE')
        .annotate(company_count=Count('companies'))
        .order_by('-company_count')[:5]
        .values_list('name', 'company_count')
    )
    top_country_names = [c[0] for c in top_countries]

    # 6. Per-Country Monthly Distribution (for Bar Chart)
    country_monthly_qs = (
        results_qs.filter(period__payroll__company__country__name__in=top_country_names)
        .annotate(month=TruncMonth('period__payment_date'))
        .values('month', 'period__payroll__company__country__name')
        .annotate(count=Count('id'))
    )

    bar_datasets_raw = []
    for country in top_country_names:
        country_data = []
        for stat in monthly_stats:
            match = next(
                (item['count'] for item in country_monthly_qs 
                 if item['month'] == stat['month'] and item['period__payroll__company__country__name'] == country), 
                0
            )
            country_data.append(match)
        
        bar_datasets_raw.append({
            'label': country,
            'data': country_data
        })

    return {
        'active_countries_count': Country.objects.filter(companies__account_status='ACTIVE').distinct().count(),
        'active_companies_count': active_companies_qs.count(),
        'user_employees_count': active_headcount,
        'payrolls_completed_count': results_qs.values('period').distinct().count(),
        'total_payslips_processed': total_payslips,
        'total_gross_amount': total_gross_amount,
        'total_net_amount': total_net_amount,
        'user_companies': active_companies_qs.order_by('-company_id')[:5],
        'country_stats': top_countries,
        'bar_labels': json.dumps(bar_labels),
        'bar_datasets_raw': json.dumps(bar_datasets_raw),
        'payslip_trend_data': json.dumps(payslip_trend_data),
        'gross_value_trend': json.dumps(gross_value_trend),
        'net_value_trend': json.dumps(net_value_trend),
        'chart_labels': json.dumps(top_country_names),
        'chart_data': json.dumps([c[1] for c in top_countries]),
    }








@login_required
@role_required("EXEC")
def dashboard_exec(request):
    return render(request, 'dashboard/exec/index.html', get_dashboard_context(request))

@login_required
@role_required("EXEC", "admin")
def dashboard_admin(request):
    return render(request, 'dashboard/admin/index.html', get_dashboard_context(request))


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")  
def dashboard(request):
    return render(request, 'dashboard.html',get_dashboard_context(request))

# ──────────────────────────────────────────────────────────────────────────────
# 3. USER & PROFILE MANAGEMENT
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def user_list(request):
    """Admin user list with filtering and search."""
    if request.user.role not in ["EXEC","ADMIN","BILLING","IMPLEMENTATION","OPERATION", "DIRECTOR","MANAGER"]:
        return redirect("dashboard")

    users = User.objects.all()
    role_filter = request.GET.get("role")
    search_query = request.GET.get("q")

    if role_filter and role_filter != "ALL":
        users = users.filter(role=role_filter)
    if search_query:
        users = users.filter(Q(username__icontains=search_query) | Q(email__icontains=search_query))

    return render(request, "management/user_list.html", {
        "users": users,
        "roles": User.ROLE_CHOICES,
        "role_filter": role_filter or "ALL",
        "search_query": search_query or "",
    })

@login_required
@role_required("EXEC", "ADMIN")
def user_edit(request, user_id):
    """Unified edit for account and profile."""
    user_to_edit = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user_to_edit)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'account':
            form = UserEditForm(request.POST, instance=user_to_edit)
            if form.is_valid():
                form.save()
                messages.success(request, "Account settings updated.")
        elif form_type == 'personal':
            form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Personal info updated.")
        return redirect('user_edit', user_id=user_id)

    return render(request, 'profile/unified_profile.html', {
        'form': UserEditForm(instance=user_to_edit),
        'profile_form': UserProfileForm(instance=profile),
        'target_user': user_to_edit
    })

@login_required
def unified_profile(request, user_id=None):
    """Unified profile view for viewing/editing."""
    target_user = get_object_or_404(User, id=user_id) if user_id else request.user
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
        return redirect(request.path)

    return render(request, "profile/unified_profile.html", {
        "target_user": target_user,
        "profile": profile,
        "profile_form": UserProfileForm(instance=profile),
        "is_own_profile": (request.user == target_user)
    })

# ──────────────────────────────────────────────────────────────────────────────
# 4. UTILITIES & SESSION
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def heartbeat(request):
    """Session keep-alive."""
    request.session['last_activity'] = time.time()
    return JsonResponse({'status': 'active', 'user': request.user.username})
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def role_based_redirect(request):
    user = request.user
    role = getattr(user, 'role', 'EMPLOYEE')  # Default to EMPLOYEE if not set

    # Mapping logic based on your requirements
    if role == 'EXEC':
        return redirect('/dashboard/exec/')
    
    elif role == 'ADMIN':
        return redirect('/dashboard/admin/')
    
    elif role in ['IMPLEMENTATION', 'BILLING', 'COMPLIANCE', 'OPERATION']:
        return redirect('/dashboard/general/')
    
    elif role == 'EMPLOYEE':
        return redirect('/dashboard/employee/')
    
    # "Client" roles (DIRECTOR, MANAGER, specialist and finance) or any other fallback
    return redirect('/dashboard/')