import csv
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse

# Models
from Exactus.company.models import Company
from Exactus.country.models import Country

# Forms & Helpers
from Exactus.company.registry import get_company_form_class   
from Exactus.company.utils.csv_importer import import_from_csv
from Exactus.company.forms.utils import get_company_form_for_country
# Added missing import
from Exactus.company.forms import CompanyUploadForm 

# Permissions - FIXED: Use the v3.1 compatible decorator we updated earlier
from Exactus.country.utils.decorators import role_required

# ────────────────────────────────────────────────────────────────
# 🧩 Company Index
# ────────────────────────────────────────────────────────────────

from django.db.models import Count, Q, Exists, OuterRef
from Exactus.payroll.models import Payroll  # Import Payroll model



@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
               "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
def company(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    
    GLOBAL_ACCESS_ROLES = ['EXEC', 'ADMIN', 'OPERATION', 'COMPLIANCE', 'BILLING', 'IMPLEMENTATION']
    
    # 1. Base Query
    if request.user.is_staff or request.user.role in GLOBAL_ACCESS_ROLES:
        queryset = Company.objects.filter(country=country)
    else:
        queryset = Company.objects.filter(
            country=country,
            authorized_users__user=request.user,
            authorized_users__is_active=True
        ).distinct()

    # 2. Add Annotations (Employees Count & Open Payroll Status)
    # We assume 'open' payrolls are those NOT completed/paid. Adjust status keys as needed.
    OPEN_STATUSES = ['DRAFT', 'OPEN', 'PROCESSING', 'review', 'pending'] 
    
    companies = queryset.annotate(
        # Count all employees linked to this company
        total_employees=Count('employees', distinct=True),
        
        # Check if ANY payroll exists with an 'open' status
        has_open_payroll=Exists(
            Payroll.objects.filter(
                company=OuterRef('pk'),
                status__in=OPEN_STATUSES 
            )
        )
    ).order_by("trade_name")

    return render(request, "company/index.html", {
        "country": country,
        "companies": companies,
        "country_slug": country.slug
    })


# ────────────────────────────────────────────────────────────────
# ➕ Create Company
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def company_create(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    
    # Get the specific class (e.g., UnitedKingdomCompanyForm)
    FormClass = get_company_form_for_country(country)

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                instance = form.save(commit=False)
                instance.country = country  # Attach country manually
                instance.save()
                messages.success(request, f"Company '{instance.trade_name}' created successfully!")
                return redirect("companies:company", country.slug)
            except Exception as e:
                messages.error(request, f"Error saving company: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FormClass()

    return render(request, "company/form.html", {
        "form": form,
        "country": country,
        "company": None,
    })


# ────────────────────────────────────────────────────────────────
# ✏️ Edit Company
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def company_edit(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    
    # Get the specific class
    FormClass = get_company_form_for_country(country)

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=company)
        
        if form.is_valid():
            try:
                instance = form.save(commit=False)
                instance.country = country
                instance.save()
                messages.success(request, f"Company '{instance.trade_name}' updated successfully!")
                return redirect("companies:company", country.slug)
            except Exception as e:
                messages.error(request, f"Error updating company: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FormClass(instance=company)

    return render(request, "company/form.html", {
        "form": form,
        "country": country,
        "company": company,
    })


# ────────────────────────────────────────────────────────────────
# 🗑 Delete Listing
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def company_delete(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country).order_by("trade_name")

    return render(request, "company/delete.html", {
        "country": country,
        "companies": companies,
        "country_slug": country.slug
    })


# ────────────────────────────────────────────────────────────────
# 📤 Upload Company CSV
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "IMPLEMENTATION")
def company_upload_view(request, country_slug=None):
    country = None

    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    if request.method == "POST":
        form = CompanyUploadForm(request.POST, request.FILES)

        if form.is_valid():
            dry_run = form.cleaned_data.get("dry_run", False)
            try:
                result = import_from_csv("companies", request.FILES["file"], dry_run=dry_run, country=country)
                request.session["upload_result"] = result

                if country_slug:
                    return redirect("companies:company_upload_result", country_slug=country_slug)
                return redirect("companies:company_upload_result_global")

            except Exception as e:
                messages.error(request, f"Upload error: {str(e)}")

    else:
        form = CompanyUploadForm()

    return render(request, "company/upload_form.html", {
        "form": form,
        "country": country,
        "country_slug": country_slug
    })


# ────────────────────────────────────────────────────────────────
# 📥 Upload Results
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "IMPLEMENTATION")
def company_upload_result_view(request, country_slug=None):
    result = request.session.get("upload_result", {})
    country = None

    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    return render(request, "company/upload_result.html", {
        "result": result,
        "country": country,
        "country_slug": country_slug
    })


# ────────────────────────────────────────────────────────────────
# 📄 Download CSV Template
# ────────────────────────────────────────────────────────────────

@login_required
def download_companies_template(request, country_slug=None):
    response = HttpResponse(content_type="text/csv")
    filename = "companies_import_template.csv"

    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
        filename = f"companies_{country.iso2_code}_template.csv"

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    # Headers matching the current model
    writer.writerow([
        "country_code", "company_code", "company_number", "trade_name", "legal_name",
        "building_name", "road_name_1", "road_name_2", "town", "post_code",
        "tax_id_01", "tax_id_02", "tax_id_03", "tax_id_04", "tax_id_05",
        "rti_user_id", "rti_password", "account_status"
    ])

    writer.writerow([
        "GB", "COMP001", "12345678", "Example Ltd", "Example Trading Ltd",
        "Tech House", "123 High St", "", "London", "EC1 1AA",
        "PAYE123", "REF456", "", "", "",
        "user_rti", "pass123", "ACTIVE"
    ])

    return response


# ────────────────────────────────────────────────────────────────
# 🧪 TEST VALIDATION VIEW
# ────────────────────────────────────────────────────────────────

def company_test_validation(request, country_slug):
    """Test view to check form validation without saving"""
    country = get_object_or_404(Country, slug=country_slug)
    FormClass = get_company_form_class(country)
    
    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, country=country)
        if form.is_valid():
            return HttpResponse("Form would save successfully!")
        else:
            return HttpResponse(f"Form validation failed. Errors: {form.errors}")
    
    # Show a simple test form
    html = f"""
    <html>
    <body>
        <h1>Test Form Validation for {country.name}</h1>
        <form method="post">
            <input type="hidden" name="country_code" value="{country.iso2_code}">
            <h3>Required Fields:</h3>
    """
    
    test_form = FormClass(country=country)
    
    for field_name, field in test_form.fields.items():
        if field.required:
            html += f"""
            <div style="margin-bottom: 10px;">
                <label>{field.label or field_name} {'(required)' if field.required else ''}</label><br>
                <input type="text" name="{field_name}" placeholder="Enter {field.label or field_name}">
            </div>
            """
    
    html += """
            <button type="submit">Test Validation</button>
        </form>
    </body>
    </html>
    """
    
    return HttpResponse(html)


# ────────────────────────────────────────────────────────────────
# 🐛 DEBUG VIEWS
# ────────────────────────────────────────────────────────────────

def company_debug_info(request, country_slug):
    """Display debug information from previous form submission"""
    country = get_object_or_404(Country, slug=country_slug)
    
    debug_info = request.session.get('debug_info', {})
    validation_errors = request.session.get('validation_errors', {})
    
    # Clear session data after displaying
    if 'debug_info' in request.session:
        del request.session['debug_info']
    if 'validation_errors' in request.session:
        del request.session['validation_errors']
    
    return render(request, "company/debug_info.html", {
        "country": country,
        "debug_info": debug_info,
        "validation_errors": validation_errors,
    })


def company_validate_ajax(request, country_slug):
    """AJAX endpoint for real-time validation"""
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        country = get_object_or_404(Country, slug=country_slug)
        FormClass = get_company_form_class(country)
        
        # Create form with POST data
        form = FormClass(request.POST, request.FILES, country=country)
        
        # Check validation
        is_valid = form.is_valid()
        
        # Prepare response
        response_data = {
            'valid': is_valid,
            'errors': form.errors,
            'cleaned_data': form.cleaned_data if is_valid else {},
        }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def company_field_requirements(request, country_slug):
    """API endpoint to get field requirements for a country"""
    country = get_object_or_404(Country, slug=country_slug)
    FormClass = get_company_form_class(country)
    
    form = FormClass(country=country)
    
    requirements = {}
    for field_name, field in form.fields.items():
        requirements[field_name] = {
            'label': str(field.label),
            'required': field.required,
            'help_text': str(field.help_text or ''),
            'type': field.__class__.__name__,
        }
    
    return JsonResponse({
        'country': country.iso2_code,
        'requirements': requirements,
    })


# ────────────────────────────────────────────────────────────────
# 📝 FORM TEMPLATE DEBUG VIEW
# ────────────────────────────────────────────────────────────────

def company_form_debug(request, country_slug):
    """Render form with debug information visible"""
    country = get_object_or_404(Country, slug=country_slug)
    FormClass = get_company_form_class(country)
    
    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, country=country)
    else:
        form = FormClass(country=country)
    
    # Analyze form structure
    form_analysis = {
        'total_fields': len(form.fields),
        'required_fields': [],
        'optional_fields': [],
        'hidden_fields': [],
        'choice_fields': [],
    }
    
    for field_name, field in form.fields.items():
        field_info = {
            'name': field_name,
            'label': str(field.label),
            'required': field.required,
            'widget': field.widget.__class__.__name__,
            'help_text': str(field.help_text or ''),
        }
        
        if field.required:
            form_analysis['required_fields'].append(field_info)
        else:
            form_analysis['optional_fields'].append(field_info)
        
        if hasattr(field.widget, 'input_type') and field.widget.input_type == 'hidden':
            form_analysis['hidden_fields'].append(field_info)
        
        if hasattr(field, 'choices') and field.choices:
            form_analysis['choice_fields'].append(field_info)
    
    return render(request, "company/form_debug.html", {
        "form": form,
        "country": country,
        "company": None,
        "form_analysis": form_analysis,
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ClientGroup
from .forms import ClientGroupForm
from Exactus.utils.decorators import role_required

@login_required
@role_required("EXEC", "ADMIN", "OPERATION")
def client_group_list(request, country_slug):
    """List all client groups."""
    groups = ClientGroup.objects.prefetch_related('companies').all()
    return render(request, 'company/client_group_list.html', {
        'groups': groups,
        'country_slug': country_slug  # Pass to template for breadcrumbs
    })

@login_required
@role_required("EXEC", "ADMIN", "OPERATION")
def client_group_create(request, country_slug):
    """Create a new client group."""
    if request.method == 'POST':
        form = ClientGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, f"Client Group '{group.name}' created successfully.")
            return redirect('company:client_group_list', country_slug=country_slug)
    else:
        form = ClientGroupForm()
    
    return render(request, 'company/client_group_form.html', {
        'form': form, 
        'title': 'Create Client Group',
        'country_slug': country_slug
    })

@login_required
@role_required("EXEC", "ADMIN", "OPERATION")
def client_group_edit(request, country_slug, group_id):
    """Edit an existing client group."""
    group = get_object_or_404(ClientGroup, pk=group_id)
    
    if request.method == 'POST':
        form = ClientGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client Group '{group.name}' updated successfully.")
            return redirect('company:client_group_list', country_slug=country_slug)
    else:
        form = ClientGroupForm(instance=group)
    
    return render(request, 'company/client_group_form.html', {
        'form': form, 
        'title': f'Edit {group.name}',
        'country_slug': country_slug
    })