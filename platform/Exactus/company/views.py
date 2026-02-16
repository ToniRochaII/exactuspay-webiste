import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Q, Count

# Models
from Exactus.country.models import Country
from Exactus.company.models import Company, ClientGroup
from Exactus.company.forms import CompanyForm, ClientGroupForm, CompanyUploadForm
from Exactus.accounts.models import UserContext
from .forms import UserAllocationForm

# Utils & Decorators
from Exactus.company.utils.csv_importer import import_companies_from_csv
from Exactus.accounts.utils.decorators import role_required, company_access_required

# -------------------------------------------------------------------
# GLOBAL / UPLOAD VIEWS (Restricted to Power Users)
# -------------------------------------------------------------------

@login_required
@role_required("EXEC", "ADMIN")
def company_upload_view(request, country_slug=None):
    """Restricted to EXEC and ADMIN."""
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    is_global = (country is None)
    
    if request.method == "POST":
        form = CompanyUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data.get("csv_file")
            dry_run = form.cleaned_data.get("dry_run", False)

            if csv_file is None:
                messages.error(request, "No file was found in the upload.")
                return render(request, "company/upload_form.html", {
                    "form": form, "country": country, "is_global": is_global
                })

            try:
                data_set = csv_file.read().decode("utf-8-sig")
            except UnicodeDecodeError:
                csv_file.seek(0)
                data_set = csv_file.read().decode("iso-8859-1")
            except AttributeError:
                messages.error(request, "Invalid file object.")
                return render(request, "company/upload_form.html", {
                    "form": form, "country": country, "is_global": is_global
                })
            
            io_string = io.StringIO(data_set)
            success_count, error_count, errors = import_companies_from_csv(
                io_string, country=country, dry_run=dry_run
            )

            request.session["upload_results"] = {
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors,
                "country_slug": country_slug,
            }

            if country:
                return redirect(reverse("companies:company_upload_result", kwargs={"country_slug": country_slug}))
            else:
                return redirect("companies:company_upload_result_global")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CompanyUploadForm()

    return render(request, "company/upload_form.html", {
        "form": form, "country": country, "is_global": is_global
    })


@login_required
@role_required("EXEC", "ADMIN")
def company_upload_result_view(request, country_slug=None):
    """Restricted to EXEC and ADMIN."""
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
        
    results = request.session.pop("upload_results", None)
    if not results:
        if country:
            return redirect("companies:company", country_slug=country_slug)
        return redirect("dashboard")

    return render(request, "company/upload_result.html", {
        "country": country, "results": results
    })


@login_required
@role_required("EXEC", "ADMIN")
def download_companies_template(request, country_slug=None):
    """Restricted to EXEC and ADMIN."""
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    response = HttpResponse(content_type='text/csv')
    filename = f"companies_template_{country.iso2_code}.csv" if country else "companies_template_GLOBAL.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    headers = []
    if not country:
        headers.append("country_code")
        
    headers.extend([
        "company_code", "company_number", "trade_name", "legal_name",
        "building_name", "road_name_1", "road_name_2", "town", "post_code",
        "tax_id_01", "tax_id_02", "tax_id_03", "tax_id_04", "tax_id_05",
        "rti_user_id", "rti_password", "account_status"
    ])
    writer.writerow(headers)

    row = []
    if not country:
        row.append("GB")
    row.extend([
        "COMP001", "12345678", "Example Trading", "Example Ltd",
        "10 Downing St", "Westminster", "", "London", "SW1A 2AA",
        "PAYE123", "", "", "", "",
        "user_rti", "pass123", "ACTIVE"
    ])
    writer.writerow(row)
    return response

# -------------------------------------------------------------------
# STANDARD CRUD VIEWS (With Isolation Logic)
# -------------------------------------------------------------------


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
def company(request, country_slug):
    """
    List companies in a specific country with total employee counts.
    """
    country = get_object_or_404(Country, slug=country_slug)
    
    global_roles = ["EXEC", "ADMIN", "COMPLIANCE"] 
    user_role = getattr(request.user, "role", "").upper()
    
    # 2. Determine the base QuerySet
    if request.user.is_superuser or user_role in global_roles:
        # Global View
        qs = Company.objects.filter(country=country)
    else:
        # Restricted View
        assigned_company_ids = request.user.contexts.values_list('company_id', flat=True)
        qs = Company.objects.filter(
            country=country,
            pk__in=assigned_company_ids
        )

    # 3. Add the Employee Count Annotation
    # FIX: Used 'employees' instead of 'employee_set' based on your model definition
    companies = qs.annotate(total_employees=Count('employees')).order_by('trade_name')

    context = {
        "country": country,
        "country_slug": country_slug,
        "companies": companies,
    }

    return render(request, "company/index.html", context)

@login_required
@role_required("EXEC", "ADMIN", "IMPLEMENTATION", "COMPLIANCE")
def company_create(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    FormClass = get_company_form(country)

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.country = country
            comp.save()
            if hasattr(form, "save_m2m"):
                form.save_m2m()
            messages.success(request, "Company created successfully.")
            return redirect('companies:company', country_slug=country.slug)
    else:
        form = FormClass()

    return render(request, 'company/form.html', {'form': form, 'country': country})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "DIRECTOR", "MANAGER", "SPECIALIST")
@company_access_required
def company_dashboard(request, country_slug, company_id): 
    # (Note: This function name might be 'company_detail' or 'company_edit' in your code)
    country = get_object_or_404(Country, slug=country_slug)
    # Use pk=company_id to match your custom primary key
    company = get_object_or_404(Company, pk=company_id)

    return render(request, 'company/dashboard.html', {
        'company': company,
        'country': country
    })

from Exactus.company.forms import CompanyForm
from Exactus.company.forms.brazil_company_form import BrazilCompanyForm

def get_company_form(country):
    return BrazilCompanyForm if country.iso2_code == "BR" else CompanyForm

@login_required
@role_required("EXEC", "ADMIN", "IMPLEMENTATION", "COMPLIANCE")
def company_edit(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id, country=country)

    FormClass = get_company_form(country)

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company updated successfully.")
            return redirect('companies:company', country_slug=country.slug)
    else:
        form = FormClass(instance=company)

    return render(request, 'company/form.html', {'form': form, 'company': company, 'country': country})


@login_required
@role_required("EXEC", "ADMIN")
def company_delete(request, country_slug, company_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id, country=country)
    
    if request.method == "POST":
        company.delete()
        messages.success(request, "Company deleted successfully.")
        return redirect('companies:company', country_slug=country.slug)
    return render(request, 'company/delete.html', {'company': company, 'country': country})

# -------------------------------------------------------------------
# CLIENT GROUPS & DEBUG VIEWS
# -------------------------------------------------------------------

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION")
def client_group_list(request, country_slug):
    # FIX: Handle the 'global' keyword to avoid 404 error
    if country_slug == 'global':
        groups = ClientGroup.objects.all()
        return render(request, 'company/client_group_list.html', {
            'groups': groups, 
            'is_global': True,  # Flag for the template
            'country': None     # No specific country
        })
        
    # Standard logic for specific countries
    country = get_object_or_404(Country, slug=country_slug)
    groups = ClientGroup.objects.filter(country=country)
    return render(request, 'company/client_group_list.html', {
        'groups': groups, 
        'country': country
    })




@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION")
def client_group_create(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    if request.method == "POST":
        form = ClientGroupForm(request.POST)
        if form.is_valid():
            grp = form.save(commit=False)
            grp.country = country
            grp.save()
            messages.success(request, "Client Group created.")
            return redirect('companies:client_group_list', country_slug=country.slug)
    else:
        form = ClientGroupForm()
    # Note: Ensure this template name matches your file structure
    return render(request, 'company/client_group_form.html', {'form': form, 'country': country})

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION")
def client_group_edit(request, country_slug, group_id):
    country = get_object_or_404(Country, slug=country_slug)
    group = get_object_or_404(ClientGroup, id=group_id, country=country)
    if request.method == "POST":
        form = ClientGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, "Client Group updated.")
            return redirect('companies:client_group_list', country_slug=country.slug)
    else:
        form = ClientGroupForm(instance=group)
    # Note: Consistency check - used 'company/groups/form.html' before, now 'client_group_form.html'
    return render(request, 'company/client_group_form.html', {'form': form, 'country': country})

# -------------------------------------------------------------------
# DEBUG VIEWS (Can be removed in production)
# -------------------------------------------------------------------
@login_required
@role_required("EXEC", "ADMIN")
def company_test_validation(request, country_slug): 
    return HttpResponse("Debug: Test Validation")

@login_required
@role_required("EXEC", "ADMIN")
def company_form_debug(request, country_slug): 
    return HttpResponse("Debug: Form Debug")

@login_required
@role_required("EXEC", "ADMIN")
def company_debug_info(request, country_slug): 
    return HttpResponse("Debug: Info")

@login_required
@role_required("EXEC", "ADMIN")
def company_validate_ajax(request, country_slug): 
    return HttpResponse("Debug: Ajax")

@login_required
@role_required("EXEC", "ADMIN")
def company_field_requirements(request, country_slug): 
    return HttpResponse("Debug: Requirements")


# -------------------------------------------------------------------
# USER ALLOCATION & ACCESS VIEWS
# -------------------------------------------------------------------

@login_required
@role_required("EXEC", "ADMIN")
def user_allocation_view(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    
    if request.method == "POST":
        form = UserAllocationForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            role = form.cleaned_data['role']
            assign_type = form.cleaned_data['assign_type']
            
            if assign_type == "COMPANY":
                company = form.cleaned_data['company']
                UserContext.objects.update_or_create(
                    user=user, 
                    company=company,
                    defaults={'role': role}
                )
                count = 1
                
            elif assign_type == "GROUP":
                group = form.cleaned_data['client_group']
                count = 0
                for company in group.companies.all():
                    UserContext.objects.update_or_create(
                        user=user, 
                        company=company,
                        defaults={'role': role}
                    )
                    count += 1
            
            messages.success(request, f"Successfully assigned {user.email} to {count} companies as {role}.")
            return redirect('companies:user_allocation', country_slug=country.slug)
    else:
        form = UserAllocationForm()

    return render(request, 'company/allocation.html', {
        'form': form, 
        'country': country
    })


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER")
@company_access_required
def company_access_list(request, country_slug, company_id):
    """
    Shows a list of all users assigned to this specific company.
    """
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)

    # Fetch all UserContext records for this company
    # select_related('user') optimizes the DB query to fetch User details in one go
    access_list = UserContext.objects.filter(company=company).select_related('user').order_by('role', 'user__email')

    return render(request, 'company/access_list.html', {
        'company': company,
        'country': country,
        'access_list': access_list
    })