from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

from Exactus.company.models import  Company 
from Exactus.country.models import Country
from Exactus.company.forms import CompanyForm
from Exactus.country.utils.decorators import role_required 


# ────────────────────────────────────────────────────────────────
# 🔍 Utility Functions
# ────────────────────────────────────────────────────────────────

def is_admin(user):
    """Helper: returns True if user has an Admin profile role."""
    return hasattr(user, "profile") and user.profile.role == "ADMIN"


# ────────────────────────────────────────────────────────────────
# 🧩 Company Pages
# ────────────────────────────────────────────────────────────────


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def company(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country).order_by("trade_name")
    return render(request, "company/index.html", {"country": country, "companies": companies, "country_slug": country.slug})


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def company_create(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)


    if request.method == "POST":
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.country = country
            company.save()
            messages.success(request, f"Company '{company.trade_name}' added successfully.")
            return redirect("companies:company", country_slug=country.slug)
    else:
        form = CompanyForm()

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

    if request.method == "POST":
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect("companies:company", country_slug=country.slug)
    else:
        form = CompanyForm(instance=company)

    return render(request, "company/edit.html", {"form": form, "country": country, "country_slug":country_slug})


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def company_delete(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country).order_by("trade_name")
    return render(request, "company/delete.html", {"country": country, "companies": companies, "country_slug": country.slug})


# Add these imports at the top of company/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
import csv
from .utils.csv_importer import import_from_csv
from .forms import CompanyUploadForm

# Add these views to the existing company/views.py
@staff_member_required
def company_upload_view(request, country_slug=None):
    """
    Upload companies via CSV. Can be country-specific or global.
    """
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    if request.method == "POST":
        form = CompanyUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            
            try:
                result = import_from_csv("companies", request.FILES["file"], dry_run=dry_run)
                request.session["upload_result"] = result
                
                if country_slug:
                    return redirect("companies:company_upload_result", country_slug=country_slug)
                else:
                    return redirect("companies:company_upload_result")
                    
            except Exception as e:
                messages.error(request, f"Upload error: {str(e)}")
    else:
        form = CompanyUploadForm()

    context = {
        "form": form,
        "country": country,
        'country_slug': country_slug
    }
    if country:
        context["country_slug"] = country_slug
        
    return render(request, "company/upload_form.html", context)

@staff_member_required
def company_upload_result_view(request, country_slug=None):
    """
    Display upload results.
    """
    result = request.session.get("upload_result", {})
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
    
    context = {
        "result": result,
        "country": country,
        'country_slug': country_slug
    }
    if country:
        context["country_slug"] = country_slug
        
    return render(request, "company/upload_result.html", context)

@staff_member_required
def download_companies_template(request, country_slug=None):
    """Download a CSV template for companies imports"""
    response = HttpResponse(content_type='text/csv')
    filename = "companies_import_template.csv"
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
        filename = f"companies_{country.iso2_code}_template.csv"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Header row
    writer.writerow([
        'country_code', 'company_code', 'company_number', 'trade_name', 'legal_name',
        'building_name', 'road_name_1', 'road_name_2', 'town', 'post_code',
        'tax_id_1', 'tax_id_2', 'tax_id_3', 'tax_id_4', 'tax_id_5',
        'tax_id_6', 'tax_id_7', 'tax_id_8', 'tax_id_9', 'tax_id_10',
        'rti_user_id', 'rti_password', 'account_status', 'account_archive'
    ])
    
    # Sample data rows
    writer.writerow([
        'US', 'COMP001', '123456789', 'Tech Solutions Inc', 'Tech Solutions Incorporated',
        'Tech Tower', '123 Innovation Ave', 'Suite 500', 'San Francisco', '94105',
        '123-45-6789', '', '', '', '', '', '', '', '', '',
        'us_rti_user', 'securepass123', 'ACTIVE', 'N'
    ])
    writer.writerow([
        'GB', 'COMP002', 'GB987654321', 'London Trading Co', 'London Trading Company Ltd',
        'Business Plaza', '45 Commerce Street', 'Floor 3', 'London', 'EC1A 1BB',
        'AB123456C', '', '', '', '', '', '', '', '', '',
        'gb_rti_user', 'securepass456', 'ACTIVE', 'N'
    ])
    
    return response



