import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse

# Models
from Exactus.country.models import Country
from Exactus.company.models import Company, ClientGroup
from Exactus.company.forms import CompanyForm, ClientGroupForm, CompanyUploadForm

# Utils
from Exactus.company.utils.csv_importer import import_companies_from_csv
from Exactus.country.utils.decorators import role_required


# -------------------------------------------------------------------
# GLOBAL / UPLOAD VIEWS
# -------------------------------------------------------------------

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")
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

    return render(
        request,
        "company/upload_form.html",
        {
            "form": form,
            "country": country,
            "is_global": is_global
        }
    )


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS",)
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
        "country": country,
        "results": results
    })


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")
def download_companies_template(request, country_slug=None):
    """Restricted to EXEC and ADMIN."""
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    response = HttpResponse(content_type='text/csv')
    
    if country:
        filename = f"companies_template_{country.iso2_code}.csv"
    else:
        filename = "companies_template_GLOBAL.csv"
        
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    # 1. Define Headers
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

    # 2. Add Example Row
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
# STANDARD CRUD VIEWS
# -------------------------------------------------------------------

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS", "DIRECTOR", "MANAGER", "BILLING", "SPECIALIST", "FINANCE")
def company(request, country_slug):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country)
    return render(request, 'company/index.html', {'companies': companies, 'country': country})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")  
def company_create(request, country_slug):
    """
    Only users with EXEC, ADMIN, or COMPLIANCE roles can access this.
    Others are bounced to the dashboard.
    """
    country = get_object_or_404(Country, slug=country_slug)
    
    if request.method == "POST":
        form = CompanyForm(request.POST)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.country = country
            comp.save()
            messages.success(request, "Company created successfully.")
            return redirect('companies:company', country_slug=country.slug)
    else:
        form = CompanyForm()
    
    return render(request, 'company/form.html', {'form': form, 'country': country})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS")
def company_edit(request, country_slug, company_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, id=company_id, country=country)
    if request.method == "POST":
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company updated successfully.")
            return redirect('companies:company', country_slug=country.slug)
    else:
        form = CompanyForm(instance=company)
    return render(request, 'company/edit.html', {'form': form, 'company': company, 'country': country})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")
def company_delete(request, country_slug, company_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, id=company_id, country=country)
    if request.method == "POST":
        company.delete()
        messages.success(request, "Company deleted successfully.")
        return redirect('companies:company', country_slug=country.slug)
    return render(request, 'company/delete.html', {'company': company, 'country': country})

# -------------------------------------------------------------------
# CLIENT GROUPS & DEBUG VIEWS
# -------------------------------------------------------------------

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS", "DIRECTOR", "MANAGER")
def client_group_list(request, country_slug):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    groups = ClientGroup.objects.filter(country=country)
    return render(request, 'company/groups/list.html', {'groups': groups, 'country': country})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")
def client_group_create(request, country_slug):
    """Restricted to EXEC and ADMIN."""
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
    return render(request, 'company/groups/form.html', {'form': form, 'country': country})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATIONS")
def client_group_edit(request, country_slug, group_id):
    """Restricted to EXEC and ADMIN."""
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
    return render(request, 'company/groups/form.html', {'form': form, 'country': country})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")
def company_test_validation(request, country_slug): 
    return HttpResponse("Debug: Test Validation")


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")
def company_form_debug(request, country_slug): 
    return HttpResponse("Debug: Form Debug")


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")
def company_debug_info(request, country_slug): 
    return HttpResponse("Debug: Info")


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")
def company_validate_ajax(request, country_slug): 
    return HttpResponse("Debug: Ajax")


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")
def company_field_requirements(request, country_slug): 
    return HttpResponse("Debug: Requirements")