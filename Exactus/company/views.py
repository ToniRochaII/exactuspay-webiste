"""
Company Views - Clean and Maintainable Implementation
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.db import transaction
import csv

from Exactus.country.utils.decorators import role_required
from Exactus.company.models import Company
from Exactus.country.models import Country
from Exactus.company.forms import get_company_form_class_for_country, CompanyUploadForm
from .utils.csv_importer import import_from_csv


# ────────────────────────────────────────────────────────────────
# CONSTANTS & CONFIGURATION
# ────────────────────────────────────────────────────────────────

COMPANY_MANAGEMENT_ROLES = [
    "EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION",
    "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE"
]

# ────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ────────────────────────────────────────────────────────────────

def _get_country_from_slug(country_slug):
    """Helper to get country or raise 404 with consistent error handling."""
    return get_object_or_404(Country, slug=country_slug)


def _get_company_for_country(company_id, country):
    """Helper to get company or raise 404 with consistent error handling."""
    return get_object_or_404(
        Company.objects.select_related('country'),
        company_id=company_id,
        country=country
    )


# ────────────────────────────────────────────────────────────────
# COMPANY PAGES (CORE FUNCTIONALITY)
# ────────────────────────────────────────────────────────────────

@login_required
@role_required(*COMPANY_MANAGEMENT_ROLES)
def company_list(request, country_slug):
    """
    List all companies for a specific country.
    
    Args:
        request: HttpRequest
        country_slug: Slug of the country
    
    Returns:
        Rendered template with companies list
    """
    country = _get_country_from_slug(country_slug)
    
    # Defer county to avoid database errors if column doesn't exist
    try:
        companies = Company.objects.filter(country=country).defer('county')
    except Exception as e:
        # If there's a database error, try without defer
        companies = Company.objects.filter(country=country)
    
    context = {
        "country": country,
        "companies": companies,
        "country_slug": country.slug,
        "page_title": f"Companies — {country.name}"
    }
    
    return render(request, "company/list.html", context)


@login_required
@role_required(*COMPANY_MANAGEMENT_ROLES)
def company_create(request, country_slug):
    """
    Create a new company for a specific country.
    
    Args:
        request: HttpRequest
        country_slug: Slug of the country
    
    Returns:
        Rendered template with company creation form
    """
    country = _get_country_from_slug(country_slug)
    
    try:
        form_class = get_company_form_class_for_country(country)
    except (AttributeError, NameError):
        from Exactus.company.forms import CompanyForm
        form_class = CompanyForm
    
    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    company = form.save(commit=False)
                    company.country = country
                    company.save()
                
                messages.success(request, f"Company '{company.trade_name}' created successfully.")
                return redirect("companies:company_list", country_slug=country.slug)
            
            except Exception as e:
                messages.error(request, f"Error creating company: {str(e)}")
    else:
        form = form_class()
    
    context = {
        "form": form,
        "country": country,
        "country_slug": country.slug,
        "company": None,
        "page_title": f"Create Company — {country.name}"
    }
    
    return render(request, "company/form.html", context)


@login_required
@role_required(*COMPANY_MANAGEMENT_ROLES)
def company_edit(request, country_slug, company_id):
    """
    Edit an existing company.
    
    Args:
        request: HttpRequest
        country_slug: Slug of the country
        company_id: ID of the company to edit
    
    Returns:
        Rendered template with company edit form
    """
    country = _get_country_from_slug(country_slug)
    company = _get_company_for_country(company_id, country)
    
    try:
        form_class = get_company_form_class_for_country(country)
    except (AttributeError, NameError):
        from Exactus.company.forms import CompanyForm
        form_class = CompanyForm
    
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=company)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                
                messages.success(request, f"Company '{company.trade_name}' updated successfully.")
                return redirect("companies:company_list", country_slug=country.slug)
            
            except Exception as e:
                messages.error(request, f"Error updating company: {str(e)}")
    else:
        form = form_class(instance=company)
    
    context = {
        "form": form,
        "country": country,
        "country_slug": country.slug,
        "company": company,
        "page_title": f"Edit Company — {company.trade_name}"
    }
    
    return render(request, "company/form.html", context)


@login_required
@role_required(*COMPANY_MANAGEMENT_ROLES)
def company_delete(request, country_slug, company_id):
    """
    Delete a company (confirmation page).
    
    Args:
        request: HttpRequest
        country_slug: Slug of the country
        company_id: ID of the company to delete
    
    Returns:
        Rendered template with delete confirmation
    """
    country = _get_country_from_slug(country_slug)
    company = _get_company_for_country(company_id, country)
    
    if request.method == "POST":
        try:
            company_name = company.trade_name
            company.delete()
            messages.success(request, f"Company '{company_name}' deleted successfully.")
            return redirect("companies:company_list", country_slug=country.slug)
        except Exception as e:
            messages.error(request, f"Error deleting company: {str(e)}")
    
    context = {
        "country": country,
        "company": company,
        "country_slug": country.slug,
        "page_title": f"Delete Company — {company.trade_name}"
    }
    
    return render(request, "company/delete.html", context)


# ────────────────────────────────────────────────────────────────
# BULK OPERATIONS (CSV IMPORT/EXPORT)
# ────────────────────────────────────────────────────────────────

@staff_member_required
def company_upload(request, country_slug=None):
    """
    Upload companies via CSV.
    
    Args:
        request: HttpRequest
        country_slug: Optional slug of the country
    
    Returns:
        Rendered template with upload form
    """
    country = None
    if country_slug:
        country = _get_country_from_slug(country_slug)
    
    if request.method == "POST":
        form = CompanyUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            
            try:
                result = import_from_csv("companies", request.FILES["file"], dry_run=dry_run)
                request.session["upload_result"] = result
                
                redirect_url = "companies:company_upload_result"
                if country_slug:
                    redirect_url = f"{redirect_url}_country"
                
                return redirect(redirect_url, country_slug=country_slug) if country_slug else redirect(redirect_url)
                    
            except Exception as e:
                messages.error(request, f"Upload error: {str(e)}")
    else:
        form = CompanyUploadForm()
    
    context = {
        "form": form,
        "country": country,
        "country_slug": country_slug,
        "page_title": "Upload Companies"
    }
    
    template = "company/upload_form.html"
    if country:
        template = "company/upload_form_country.html"
    
    return render(request, template, context)


@staff_member_required
def company_upload_result(request, country_slug=None):
    """
    Display upload results.
    
    Args:
        request: HttpRequest
        country_slug: Optional slug of the country
    
    Returns:
        Rendered template with upload results
    """
    result = request.session.get("upload_result", {})
    country = None
    
    if country_slug:
        country = _get_country_from_slug(country_slug)
    
    context = {
        "result": result,
        "country": country,
        "country_slug": country_slug,
        "page_title": "Upload Results"
    }
    
    template = "company/upload_result.html"
    if country:
        template = "company/upload_result_country.html"
    
    return render(request, template, context)


@staff_member_required
def download_companies_template(request, country_slug=None):
    """
    Download a CSV template for companies import.
    
    Args:
        request: HttpRequest
        country_slug: Optional slug of the country
    
    Returns:
        CSV file response
    """
    response = HttpResponse(content_type='text/csv')
    filename = "companies_import_template.csv"
    
    if country_slug:
        country = _get_country_from_slug(country_slug)
        filename = f"companies_{country.iso2_code}_template.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Header row with all fields
    headers = [
        'country_code', 'company_code', 'company_number', 'trade_name', 'legal_name',
        'building_name', 'road_name_1', 'road_name_2', 'town', 'post_code', 'county',
        'tax_id_1', 'tax_id_2', 'tax_id_3', 'tax_id_4', 'tax_id_5',
        'tax_id_6', 'tax_id_7', 'tax_id_8', 'tax_id_9', 'tax_id_10',
        'rti_user_id', 'rti_password', 'account_status', 'account_archive'
    ]
    
    writer.writerow(headers)
    
    # Sample data rows
    writer.writerow([
        'US', 'COMP001', '123456789', 'Tech Solutions Inc', 'Tech Solutions Incorporated',
        'Tech Tower', '123 Innovation Ave', 'Suite 500', 'San Francisco', '94105', 'California',
        '123-45-6789', '', '', '', '', '', '', '', '', '',
        'us_rti_user', 'securepass123', 'ACTIVE', 'N'
    ])
    writer.writerow([
        'GB', 'COMP002', 'GB987654321', 'London Trading Co', 'London Trading Company Ltd',
        'Business Plaza', '45 Commerce Street', 'Floor 3', 'London', 'EC1A 1BB', 'London',
        'AB123456C', '', '', '', '', '', '', '', '', '',
        'gb_rti_user', 'securepass456', 'ACTIVE', 'N'
    ])
    
    return response