import csv
import json
import time
import datetime
from datetime import timedelta
from collections import defaultdict
from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.apps import apps
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from django.contrib.auth import get_user_model, authenticate, login, logout as auth_logout, views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import translation
from django.db import transaction
from django.db.models import Q, Count, Sum, F
from django.db.models.functions import TruncMonth

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

# ──────────────────────────────────────────────────────────────────────────────
# UTILITY: COMPLIANCE CHECK
# ──────────────────────────────────────────────────────────────────────────────

def get_pending_regulation_updates():
    """
    Return the number of regulations that still require an update.
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

    return qs.count()


# ──────────────────────────────────────────────────────────────────────────────
# 1. PROFILE & PASSWORD VIEWS
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS", "DIRECTOR", "MANAGER")
def profile(request):
    """User's own profile - uses unified template."""
    return unified_profile(request, user_id=None)


class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done') 

    def form_valid(self, form):
        messages.info(self.request, "If your email exists, you'll receive reset instructions shortly.")
        return super().form_valid(form)


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'auth/password_reset_done.html'


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed successfully.")
        return super().form_valid(form)


class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'auth/password_reset_complete.html'


# ──────────────────────────────────────────────────────────────────────────────
# 2. USER MANAGEMENT & EXPORTS
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def export_users_csv(request):
    """Exports filtered users to CSV."""
    if request.user.role not in {"EXEC","ADMIN", "COMPLIANCE"}:
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


def form_valid(self, form):
    response = super().form_valid(form)

    lang = form.instance.preferred_language
    translation.activate(lang)
    self.request.session[translation.LANGUAGE_SESSION_KEY] = lang

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

    matrix = {
        r: {d: {a: False for a in actions} for d in domains}
        for r in roles
    }

    for row in PermissionMatrix.objects.all().only("role", "domain", "action", "allowed"):
        if row.role in matrix and row.domain in matrix[row.role]:
            matrix[row.role][row.domain][row.action] = row.allowed

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


# ──────────────────────────────────────────────────────────────────────────────
# 4. EMAIL & ACCOUNT NOTIFICATIONS
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS", "DIRECTOR", "MANAGER")
def admin_reset_password(request, user_id):
    """Sends a password reset email to a specific user."""
    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, "You cannot reset your own password here. Use the standard reset flow.")
        return redirect("user_edit", user_id=user_id)

    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = request.build_absolute_uri(reverse('password_reset_confirm', args=[uid, token]))

    subject = "Password Reset Request - Admin Initiated"
    html_message = render_to_string("emails/admin_reset_password.html", {
        "user": user,
        "reset_url": reset_url,
    })
    plain_message = strip_tags(html_message)

    try:
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False, html_message=html_message)
        messages.success(request, f"Password reset email sent to {user.email}")
    except Exception as e:
        messages.error(request, f"Failed to send email: {str(e)}")

    return redirect("user_edit", user_id=user_id)


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS", "DIRECTOR", "MANAGER")
def resend_welcome_email(request, user_id):
    """Manually resend the welcome email."""
    user = get_object_or_404(User, id=user_id)
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    setup_url = request.build_absolute_uri(reverse('password_reset_confirm', args=[uid, token]))
    
    subject = "Welcome to Exactus - Account Details"
    context = {'user': user, 'username': user.username, 'role': user.get_role_display(), 'setup_url': setup_url, 'login_url': request.build_absolute_uri(reverse('login'))}
    html_message = render_to_string("emails/account_welcome.html", context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False, html_message=html_message)
        messages.success(request, f"Welcome email sent to {user.email}.")
    except Exception as e:
        messages.error(request, f"Error sending welcome email: {str(e)}")
        
    return redirect("user_edit", user_id=user_id)


# ──────────────────────────────────────────────────────────────────────────────
# 5. UTILITIES (BEACON, SESSION)
# ──────────────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def tab_close_detection(request):
    if request.user.is_authenticated:
        print(f"User {request.user.username} closed tab")
    return JsonResponse({'status': 'ok'})

@login_required
@require_GET
def session_status(request):
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
# 6. AUTHENTICATION & REGISTRATION
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def register(request):
    allowed_roles = {"EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER"}
    if getattr(request.user, 'role', None) not in allowed_roles:
        messages.error(request, "Access denied.")
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
                OnboardingService.onboard_employee(username=username, email=email, role=role, created_by_user=request.user)
                messages.success(request, f"User '{username}' created.")
                return redirect("user_list") 
            except Exception as e:
                messages.error(request, f"Error creating user: {str(e)}")

    return render(request, 'auth/register.html', {'roles': User.ROLE_CHOICES})

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
            if not remember_me:
                request.session.set_expiry(0)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def enhanced_logout(request):
    if request.user.is_authenticated:
        if 'last_activity' in request.session:
            del request.session['last_activity']
        auth_logout(request)
        messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


# ──────────────────────────────────────────────────────────────────────────────
# 7. DASHBOARDS
# ──────────────────────────────────────────────────────────────────────────────

def get_dashboard_context(request):
    Company = apps.get_model('company', 'Company')
    Employee = apps.get_model('employee', 'Employee')
    PayrollResult = apps.get_model('payroll', 'PayrollResult')
    Country = apps.get_model('country', 'Country')

    today = timezone.now().date()
    one_year_ago = today - timedelta(days=365)

    # 1. PAYROLL RESULTS: Filter strictly for ACTIVE companies only.
    results_qs = PayrollResult.objects.filter(
        period__payment_date__gte=one_year_ago,
        period__payroll__company__account_status='ACTIVE'
    ).select_related('period', 'period__payroll__company__country')

    totals = results_qs.aggregate(total_gross=Sum('gross_pay'), total_net=Sum('net_pay'), total_count=Count('id'))
    total_payslips = totals['total_count'] or 0
    total_gross_amount = totals['total_gross'] or 0
    total_net_amount = totals['total_net'] or 0

    monthly_stats = (
        results_qs.annotate(month=TruncMonth('period__payment_date'))
        .values('month')
        .annotate(payslip_count=Count('id'), monthly_gross=Sum('gross_pay'), monthly_net=Sum('net_pay'))
        .order_by('month')
    )

    bar_labels = [s['month'].strftime('%b %Y') for s in monthly_stats]
    payslip_trend_data = [s['payslip_count'] for s in monthly_stats]
    gross_value_trend = [float(s['monthly_gross'] or 0) for s in monthly_stats]
    net_value_trend = [float(s['monthly_net'] or 0) for s in monthly_stats]

    # 2. COMPANIES LIST: Strictly ACTIVE only.
    active_companies_qs = Company.objects.filter(account_status='ACTIVE')
    
    # 3. HEADCOUNT: Strictly employees of ACTIVE companies only.
    active_headcount = Employee.objects.filter(
        company__account_status='ACTIVE'
    ).filter(
        Q(employment_end_date__isnull=True) | Q(employment_end_date__gt=today)
    ).count()

    # 4. COUNTRY CHART STATS:
    # We use the exact same logic here: Annotate with active count, then filter > 0.
    # This ensures the chart only displays countries that actually have active companies.
    top_countries = list(
        Country.objects.annotate(
            active_company_count=Count('companies', filter=Q(companies__account_status='ACTIVE'))
        )
        .filter(active_company_count__gt=0)
        .order_by('-active_company_count')[:10]
        .values_list('name', 'active_company_count')
    )
    top_country_names = [c[0] for c in top_countries]

    # Calculate monthly stats only for the active countries found above
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
            match = next((item['count'] for item in country_monthly_qs if item['month'] == stat['month'] and item['period__payroll__company__country__name'] == country), 0)
            country_data.append(match)
        bar_datasets_raw.append({'label': country, 'data': country_data})

    return {
        # KPI: Active Countries (Must have > 0 active companies)
        # Using the specific annotation logic you requested to be 100% strict
        'active_countries_count': Country.objects.annotate(
            active_count=Count('companies', filter=Q(companies__account_status='ACTIVE'))
        ).filter(active_count__gt=0).count(),
        
        'active_companies_count': active_companies_qs.count(),
        'user_employees_count': active_headcount,
        'payrolls_completed_count': results_qs.values('period').distinct().count(),
        'total_payslips_processed': total_payslips,
        'total_gross_amount': total_gross_amount,
        'total_net_amount': total_net_amount,
        
        # LIST: "Recent Portfolio" - shows ONLY active companies.
        'user_companies': active_companies_qs.order_by('-company_id')[:5],
        
        # CHART: "Companies by Country" - shows ONLY active counts.
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
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS", "DIRECTOR", "MANAGER")
def dashboard_admin(request):
    return render(request, 'dashboard/admin/index.html', get_dashboard_context(request))


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")  
def dashboard(request):
    return render(request, 'dashboard.html', get_dashboard_context(request))


# ──────────────────────────────────────────────────────────────────────────────
# 8. USER & PROFILE MANAGEMENT VIEWS
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def user_list(request):
    """Admin user list."""
    ALLOWED_ROLES = {"EXEC", "ADMIN", "BILLING", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE"}
    if request.user.role not in ALLOWED_ROLES:
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    users = User.objects.all()
    role_filter = request.GET.get("role")
    search_query = request.GET.get("q")

    if role_filter and role_filter != "ALL":
        users = users.filter(role=role_filter)
    if search_query:
        users = users.filter(Q(username__icontains=search_query) | Q(email__icontains=search_query))

    return render(request, "management/user_list.html", {"users": users, "roles": User.ROLE_CHOICES, "role_filter": role_filter or "ALL", "search_query": search_query or ""})

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS", "DIRECTOR", "MANAGER")
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

    return render(request, 'profile/unified_profile.html', {'form': UserEditForm(instance=user_to_edit), 'profile_form': UserProfileForm(instance=profile), 'target_user': user_to_edit})

@login_required
def unified_profile(request, user_id=None):
    """Unified profile view."""
    target_user = get_object_or_404(User, id=user_id) if user_id else request.user
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save()

            # ✅ apply immediately for this session (only makes sense for own profile)
            if request.user == target_user:
                lang = getattr(profile, "preferred_language", None)
                if lang:
                    translation.activate(lang)
                    request.session["django_language"] = lang  # ✅ simplest + reliable

            messages.success(request, "Profile updated.")
            return redirect(request.path)
    else:
        form = UserProfileForm(instance=profile)

    return render(
        request,
        "profile/unified_profile.html",
        {
            "target_user": target_user,
            "profile": profile,
            "profile_form": form,
            "is_own_profile": (request.user == target_user),
        },
    )


@login_required
def heartbeat(request):
    """Session keep-alive."""
    request.session['last_activity'] = time.time()
    return JsonResponse({'status': 'active', 'user': request.user.username})

@login_required
def role_based_redirect(request):
    role = getattr(request.user, 'role', 'EMPLOYEE') 
    if role == 'EXEC': return redirect('/dashboard/exec/')
    if role == 'ADMIN': return redirect('/dashboard/admin/')
    if role in ['IMPLEMENTATION', 'BILLING', 'COMPLIANCE', 'OPERATION']: return redirect('/dashboard/')
    if role == 'EMPLOYEE': return redirect('/ess/dashboard/')
    return redirect('/dashboard/')


@login_required
def switch_context(request, company_id):
    """
    Redirects the user to the specific dashboard for the selected company.
    """
    company = get_object_or_404(Company, pk=company_id)
    if not request.user.contexts.filter(company=company).exists() and not request.user.is_superuser:
         messages.error(request, "Access Denied.")
         return redirect("dashboard")

    return redirect(
        'companies:company_dashboard', 
        country_slug=company.country.slug, 
        company_id=company.pk
    )

# ──────────────────────────────────────────────────────────────────────────────
# 9. MAP DATA (Ensures strict filtering for Map as well)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def dashboard_country_map(request):
    """
    Returns list of country codes that have at least one ACTIVE company.
    Applies strict annotation filtering to match the KPI logic.
    """
    Country = apps.get_model('country', 'Country')
    
    # Using the same logic as the KPI to ensure consistency:
    # 1. Annotate active count
    # 2. Filter > 0
    active_country_codes = list(
        Country.objects.annotate(
            active_count=Count('companies', filter=Q(companies__account_status='ACTIVE'))
        )
        .filter(active_count__gt=0)
        .values_list('iso_code', flat=True)
    )
    
    return JsonResponse({'countries': active_country_codes})

from django.conf import settings
from django.utils import translation

class UserPreferredLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            profile = getattr(user, "userprofile", None)  # or user.profile if you set related_name
            lang = getattr(profile, "preferred_language", None)

            if lang and lang in dict(settings.LANGUAGES):
                translation.activate(lang)
                request.LANGUAGE_CODE = lang
                request.session["django_language"] = lang

        response = self.get_response(request)
        translation.deactivate()
        return response


