from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

import csv
from datetime import timedelta
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model, logout, authenticate, login, views as auth_views
from django.db import transaction
from django.db.models import Q, Count, F
from django.db.models.functions import TruncMonth
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
import json

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


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from Exactus.accounts.models import User
from Exactus.accounts.services.onboarding import OnboardingService

@login_required
def register(request):
    """
    Admin user creation that triggers the Two-Email Onboarding flow.
    """
    # 1. Permission Check
    allowed_roles = {"EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER"}
    
    # Safely handle users without a role attribute if necessary, though your model defaults to EMPLOYEE
    user_role = getattr(request.user, 'role', None)
    
    if user_role not in allowed_roles:
        messages.error(request, "Access denied: only administrators can create new users.")
        return redirect("dashboard")

    if request.method == 'POST':
        # We only need basic details, password will be auto-generated
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        # Basic validation
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            try:
                # 2. Call the Onboarding Service
                # This generates the password, sets the flag, and sends the 2 emails
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

    # Load roles for the dropdown
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
    """User's own profile - uses unified template."""
    return unified_profile(request, user_id=None)


@login_required
def dashboard_admin(request):
    """Admin/Executive dashboard with platform analytics."""
    # Check if user has admin/exec permissions
    if not hasattr(request.user, 'role') or request.user.role not in ['EXEC', 'ADMIN']:
        messages.error(request, "You don't have permission to access the admin dashboard.")
        return redirect('dashboard')
    
    # Generate cache key
    cache_key = f'dashboard_admin_{request.user.id}_{timezone.now().strftime("%Y%m")}'
    cached_data = cache.get(cache_key)
    
    if cached_data and not request.GET.get('refresh'):
        return render(request, 'dashboard/admin.html', cached_data)
    
    now = timezone.now()
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)
    one_year_ago = now - timedelta(days=365)
    
    # Import models here to avoid circular imports
    from Exactus.country.models import Country
    from Exactus.company.models import Company
    from Exactus.employee.models import Employee
    from Exactus.payroll.models import Payroll
    
    # ──────────────── KPIs ────────────────
    
    # Country metrics - Country uses 'id' as PK
    country_stats = Country.objects.aggregate(
        active_countries=Count('id', filter=Q(status='ACTIVE')),
        implementing_countries=Count('id', filter=Q(status='IMPLEMENTING')),
        inactive_countries=Count('id', filter=Q(status='INACTIVE')),
        total_countries=Count('id')
    )
    
    # Company metrics - Company uses 'company_id' as PK
    company_stats = Company.objects.aggregate(
        active_companies=Count('company_id', filter=Q(account_status='ACTIVE')),
        suspended_companies=Count('company_id', filter=Q(account_status='SUSPENDED')),
        inactive_companies=Count('company_id', filter=Q(account_status='INACTIVE')),
        total_companies=Count('company_id')
    )
    
    # Employee metric
    total_employees = cache.get('total_employees')
    if total_employees is None:
        total_employees = Employee.objects.count()
        cache.set('total_employees', total_employees, 3600)
    
    # Payroll metrics
    total_payrolls = Payroll.objects.count()
    
    # Get payroll frequency choices safely
    try:
        PAYROLL_FREQUENCY_CHOICES = getattr(Payroll, 'PAYROLL_FREQUENCY_CHOICES', [])
        if PAYROLL_FREQUENCY_CHOICES:
            monthly_codes = [code for code, _ in PAYROLL_FREQUENCY_CHOICES 
                           if any(pattern in code.lower().replace('_', '-') 
                                 for pattern in ['monthly', 'semi-monthly', 'bi-weekly'])]
            monthly_payrolls = Payroll.objects.filter(payroll_frequency__in=monthly_codes).count()
        else:
            monthly_payrolls = 0
    except Exception:
        monthly_payrolls = 0
    
   
    
   
    
   
   
    
    # ──────────────── Map Data ────────────────
    
    # Active country codes with null check
    active_country_codes = list(
        Country.objects.filter(status='ACTIVE')
        .exclude(iso2_code__isnull=True)
        .exclude(iso2_code='')
        .values_list('iso2_code', flat=True)
    )
    
    # Get payslip counts per country with country filter
    
    
    
   
    
    # ──────────────── Top Companies (Optimized) ────────────────
    
    # Get company IDs with most payslips first
   
    
   
 
    
   
    
    # Prepare context
    context = {
        # KPIs
        'active_countries': country_stats.get('active_countries', 0),
        'implementing_countries': country_stats.get('implementing_countries', 0),
        'inactive_countries': country_stats.get('inactive_countries', 0),
        'total_countries': country_stats.get('total_countries', 0),
        
        'active_companies': company_stats.get('active_companies', 0),
        'suspended_companies': company_stats.get('suspended_companies', 0),
        'inactive_companies': company_stats.get('inactive_companies', 0),
        'total_companies': company_stats.get('total_companies', 0),
        
        'total_employees': total_employees or 0,
        'total_payrolls': total_payrolls,
        'monthly_payrolls': monthly_payrolls,
        
        # Payslip counts
        'payslips_total': payslip_stats['payslips_total'],
        'unique_employees_processed_total': unique_employees_processed_total or 0,
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


from django.shortcuts import render
from django.apps import apps
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
import json
import datetime

def dashboard(request):
    # --- Load Models ---
    Company = apps.get_model('company', 'Company')
    Employee = apps.get_model('employee', 'Employee')
    PayrollPeriod = apps.get_model('payroll', 'PayrollPeriod')
    PayrollResult = apps.get_model('payroll', 'PayrollResult')

    # --- 1. CORRECT COUNTS LOGIC ---

    # A. Active Companies
    # Counts all companies currently marked as ACTIVE
    active_companies_count = Company.objects.filter(account_status='ACTIVE').count()

    # B. Active Countries
    # This logic counts distinct countries where you have at least one active company.
    # Example: If you have 5 companies but they are all in the 'UK', this will show "1".
    active_countries_count = Company.objects.filter(account_status='ACTIVE').values('country').distinct().count()

    # --- 2. Employee Stats ---
    # Counts employees currently employed (no end date)
    user_employees_count = Employee.objects.filter(employment_end_date__isnull=True).count()
    
    # --- 3. Payroll Activity (30 Days) ---
    today = timezone.now()
    thirty_days_ago = today - datetime.timedelta(days=30)
    
    payslips_30d_count = 0
    # Only try to count if we have payroll data
    if PayrollResult.objects.exists():
        payslips_30d_count = PayrollResult.objects.filter(
            period__payment_date__gte=thirty_days_ago
        ).count()

    # --- 4. Chart Data (Financial Trend) ---
    six_months_ago = today - datetime.timedelta(days=180)
    chart_labels = []
    chart_data = []
    
    try:
        trends = PayrollPeriod.objects.filter(payment_date__gte=six_months_ago)\
            .annotate(month=TruncMonth('payment_date'))\
            .values('month')\
            .annotate(total_gross=Sum('total_gross'))\
            .order_by('month')

        chart_labels = [t['month'].strftime('%b') for t in trends]
        chart_data = [float(t['total_gross'] or 0) for t in trends]
    except Exception:
        pass # Handle empty DB gracefully

    # --- 5. Context ---
    user_companies = Company.objects.filter(account_status='ACTIVE')[:5]

    context = {
        'active_countries_count': active_countries_count,
        'active_companies_count': active_companies_count,
        'user_employees_count': user_employees_count,
        'payslips_30d_count': payslips_30d_count,
        'user_companies': user_companies,
        'notifications': [], 
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'dashboard.html', context)




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
def user_list(request):
    """Admin-only user list with filtering, search and bulk actions."""
    if request.user.role not in ["EXEC","ADMIN","BILLING","IMPLEMENTATION","OPERATION", "DIRECTOR","MANAGER"]:
        return redirect("dashboard")

    users = User.objects.all()

    # Filtering
    role_filter = request.GET.get("role")
    search_query = request.GET.get("q")

    if role_filter and role_filter != "ALL":
        users = users.filter(role=role_filter)

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    # Bulk actions
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
    """User detail view - uses unified template."""
    return unified_profile(request, user_id=user_id)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, UserProfile
from .forms import UserEditForm, UserProfileForm
from Exactus.utils.decorators import role_required

@login_required
@role_required("EXEC", "ADMIN")
def user_edit(request, user_id):
    """
    Edit a user's account AND profile using the unified profile template.
    """
    user_to_edit = get_object_or_404(User, pk=user_id)
    # Ensure a profile exists, creating one if necessary
    profile, created = UserProfile.objects.get_or_create(user=user_to_edit)

    if request.method == 'POST':
        # Determine which form is being submitted via hidden input 'form_type'
        form_type = request.POST.get('form_type')
        
        # Initialize both forms with POST data to prevent rendering errors if one fails
        user_form = UserEditForm(request.POST, instance=user_to_edit)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if form_type == 'account' or not form_type: # Default to account logic
            if user_form.is_valid():
                user_form.save()
                messages.success(request, f"Account settings for '{user_to_edit.username}' updated.")
                return redirect('user_edit', user_id=user_id)
        
        elif form_type == 'personal':
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Personal information updated.")
                return redirect('user_edit', user_id=user_id)

    else:
        # GET Request: Initialize forms with existing data
        user_form = UserEditForm(instance=user_to_edit)
        profile_form = UserProfileForm(instance=profile)

    return render(request, 'profile/unified_profile.html', {
        'form': user_form,           # Maps to {{ form }} in template
        'profile_form': profile_form, # Maps to {{ profile_form }} in template
        'user_to_edit': user_to_edit,
        'target_user': user_to_edit   # The template uses this variable for display names
    })




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


@login_required
def unified_profile(request, user_id=None):
    """Unified profile view for viewing/editing user profiles."""
    # Determine target user
    if user_id:
        target_user = get_object_or_404(User, id=user_id)
    else:
        target_user = request.user

    profile, created = UserProfile.objects.get_or_create(user=target_user)

    is_own_profile = (request.user == target_user)
    can_edit = is_own_profile or AccessControl.has_permission(request.user, "USER", "UPDATE")

    # Initialize forms
    user_form = None
    profile_form = UserProfileForm(instance=profile)
    
    if not is_own_profile:
        user_form = UserEditForm(instance=target_user)

    # POST handling
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "profile":
            profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect(request.path)
            else:
                messages.error(request, f"Profile errors: {profile_form.errors}")

        elif form_type == "personal":
            personal_form = UserProfileForm(request.POST, request.FILES, instance=profile)
            
            if personal_form.is_valid():
                personal_form.save()
                messages.success(request, "Personal information updated.")
                return redirect(request.path)
            else:
                messages.error(request, f"Personal info errors: {personal_form.errors}")

        elif form_type == "notifications" and is_own_profile:
            profile.notify_by_email = 'notify_by_email' in request.POST
            profile.notify_by_sms = 'notify_by_sms' in request.POST
            profile.save()
            messages.success(request, "Notification preferences updated.")
            return redirect(request.path)

    # Render
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


from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings

User = get_user_model()

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
def heartbeat(request):
    """Endpoint for session keep-alive requests."""
    # Update session timestamp
    request.session['last_activity'] = time.time()
    request.session.modified = True
    
    # Calculate remaining time
    last_activity = request.session.get('last_activity', time.time())
    elapsed = time.time() - last_activity
    remaining = max(300 - elapsed, 0)
    
    return JsonResponse({
        'status': 'active',
        'user': request.user.username,
        'remaining_seconds': int(remaining),
        'timestamp': timezone.now().isoformat()
    })


@csrf_exempt
@require_POST
def tab_close_detection(request):
    """Handle browser tab close notifications."""
    if request.user.is_authenticated:
        # Optional: log tab close event
        print(f"Tab closed by {request.user.username}")
        
    return JsonResponse({'status': 'ok'})


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


# Optional: Enhanced logout view
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.shortcuts import redirect


def enhanced_logout(request):
    """Custom logout that clears session data."""
    if request.user.is_authenticated:
        # Clear session data
        if 'last_activity' in request.session:
            del request.session['last_activity']
        
        auth_logout(request)
        messages.info(request, 'You have been logged out successfully.')
    
    return redirect('login')


