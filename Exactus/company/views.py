import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

# Models
from Exactus.company.models import Company 
from Exactus.country.models import Country

# Forms & Utils
from Exactus.company.forms import (
    CompanyForm, 
    CompanyUploadForm, 
    get_company_form_class_for_country # Helper function we created
)
from Exactus.company.utils.csv_importer import import_from_csv
from Exactus.country.utils.decorators import role_required 


# ────────────────────────────────────────────────────────────────
# 🧩 Company CRUD Views
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def company(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    # Order by trade name for consistency
    companies = Company.objects.filter(country=country).order_by("trade_name")
    
    context = {
        "country": country, 
        "companies": companies, 
        "country_slug": country.slug
    }
    return render(request, "company/index.html", context)


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def company_create(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    
    # 💡 REFACTORED: Dynamically get the correct form (GB, BR, AR, or Default)
    CompanyFormClass = get_company_form_class_for_country(country)
    
    if request.method == "POST":
        form = CompanyFormClass(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.country = country
            company.save()
            messages.success(request, f"Company '{company.trade_name}' added successfully.")
            return redirect("companies:company", country_slug=country.slug)
        # If invalid, fall through to re-render template with errors
    else:
        form = CompanyFormClass()
    
    return render(
        request,
        "company/create.html",
        {"form": form, "country": country, "country_slug": country.slug}
    )


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def company_edit(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id, country=country)

    # Use the specific form class so labels match the country
    CompanyFormClass = get_company_form_class_for_country(country)

    if request.method == "POST":
        form = CompanyFormClass(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company details updated successfully.")
            return redirect("companies:company", country_slug=country.slug)
    else:
        form = CompanyFormClass(instance=company)

    return render(
        request, 
        "company/edit.html", 
        {"form": form, "country": country, "country_slug": country_slug, "company": company}
    )


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def company_delete(request, country_slug):
    """
    Note: Usually delete requires an ID. This view currently lists companies TO delete.
    Make sure your template handles the actual deletion POST request.
    """
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country).order_by("trade_name")
    return render(request, "company/delete.html", {"country": country, "companies": companies, "country_slug": country.slug})


# ────────────────────────────────────────────────────────────────
# 📤 Upload & Template Views
# ────────────────────────────────────────────────────────────────

@staff_member_required
def company_upload_view(request, country_slug=None):
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    if request.method == "POST":
        form = CompanyUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            try:
                # Assuming import_from_csv handles country assignment internally if passed
                result = import_from_csv("companies", request.FILES["file"], dry_run=dry_run, country=country)
                request.session["upload_result"] = result
                
                if country_slug:
                    return redirect("companies:company_upload_result", country_slug=country_slug)
                else:
                    return redirect("companies:company_upload_result_global")
            except Exception as e:
                messages.error(request, f"Upload error: {str(e)}")
    else:
        form = CompanyUploadForm()

    context = {
        "form": form,
        "country": country,
        "country_slug": country_slug
    }
    return render(request, "company/upload_form.html", context)


@staff_member_required
def company_upload_result_view(request, country_slug=None):
    result = request.session.get("upload_result", {})
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
    
    context = {
        "result": result,
        "country": country,
        "country_slug": country_slug
    }
    return render(request, "company/upload_result.html", context)


@staff_member_required
def download_companies_template(request, country_slug=None):
    response = HttpResponse(content_type='text/csv')
    filename = "companies_import_template.csv"
    
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
        filename = f"companies_{country.iso2_code}_template.csv"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Header
    writer.writerow([
        'country_code', 'company_code', 'company_number', 'trade_name', 'legal_name',
        'building_name', 'road_name_1', 'road_name_2', 'town', 'post_code',
        'tax_id_1', 'tax_id_2', 'tax_id_3', 'tax_id_4', 'tax_id_5',
        'rti_user_id', 'rti_password', 'account_status'
    ])
    
    # Sample Row
    writer.writerow([
        'GB', 'COMP001', '12345678', 'Example Ltd', 'Example Trading Ltd',
        'Tech House', '123 High St', '', 'London', 'EC1 1AA',
        'PAYE123', 'REF456', '', '', '',
        'user_rti', 'pass123', 'ACTIVE'
    ])
    
    return response