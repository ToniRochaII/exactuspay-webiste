from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
import csv

from Exactus.country.utils.csv_importer import import_from_csv
from Exactus.country.utils.decorators import role_required
from Exactus.country.forms import CountryForm, CountryUploadForm
from django.db.models import Count, Q
from Exactus.country.models import Country

# -------------------------------------------------------------------------
# COUNTRY MANAGEMENT VIEWS
# -------------------------------------------------------------------------

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
def country(request):
    """
    List countries with a count of Calculation Bases for Fiscal Year 2025.
    
    ISOLATION LOGIC:
    - Global Roles (EXEC, ADMIN, COMPLIANCE): See ALL countries.
    - Restricted Roles (Director, Manager, etc.): See ONLY countries where they have a company assignment.
    """
    
    # 1. Base Query (Includes your specific annotation)
    # We build the query but don't execute it yet.
    base_queryset = Country.objects.annotate(
        calc_bases_2025_count=Count(
            'regulations__calculation_bases',
            filter=Q(regulations__fiscal_year=2025)
        )
    )

    # 2. Define Global Roles
    global_roles = ["EXEC", "ADMIN", "COMPLIANCE"]
    user_role = getattr(request.user, "role", "").upper()

    # 3. Filter Logic
    if request.user.is_superuser or user_role in global_roles:
        # Global View: See everything
        countries = Country.objects.filter(archive="N").order_by("name")
    else:
        # Restricted View:
        # Step A: Get IDs of companies assigned to this user (from UserContext)
        assigned_company_ids = request.user.contexts.values_list('company_id', flat=True)

        # Step B: Filter countries that contain these specific companies
        # We use 'companies__pk__in' to look up the reverse relationship from Country -> Company
        # .distinct() is crucial here so a country doesn't appear twice if user has 2 companies there.
        countries = base_queryset.filter(
            companies__pk__in=assigned_company_ids
        ).distinct().order_by('name')

    return render(request, 'country/index.html', {
        'countries': countries
    })


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def country_delete(request):
    """Show archived (deleted) countries only. Restricted to EXEC and ADMIN."""
    countries = Country.objects.filter(archive="Y").order_by("name")
    return render(request, "country/delete.html", {"countries": countries})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def country_create(request):
    """Create a new country. Restricted to EXEC and ADMIN."""
    if request.method == "POST":
        form = CountryForm(request.POST)
        if form.is_valid():
            country = form.save()
            messages.success(request, f"{country.name} created successfully.")
            return redirect("country:country")
    else:
        form = CountryForm()

    return render(request, "country/form.html", {"form": form})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def country_edit(request, slug):
    """Edit a country. Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=slug)

    if request.method == "POST":
        form = CountryForm(request.POST, instance=country)
        if form.is_valid():
            form.save()
            messages.success(request, f"{country.name} updated successfully.")
            return redirect("country:country")
    else:
        form = CountryForm(instance=country)

    return render(request, "country/form.html", {
        "form": form, 
        "country": country, 
        "country_slug": country.slug
    })


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def country_upload_view(request):
    """Upload countries via CSV. Restricted to EXEC and ADMIN."""
    if request.method == "POST":
        form = CountryUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            
            # Using the utility we imported
            result = import_from_csv("country", request.FILES["file"], dry_run=dry_run)
            
            request.session["upload_result"] = result
            return redirect("country:country_upload_result")
    else:
        form = CountryUploadForm()

    return render(request, "country/upload_form.html", {"form": form})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def country_upload_result_view(request):
    """View upload results. Restricted to EXEC and ADMIN."""
    result = request.session.get("upload_result")
    return render(request, "country/upload_result.html", {"result": result})


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def download_csv_template(request):
    """Download a CSV template for country imports. Restricted to EXEC and ADMIN."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="country_import_template.csv"'
    
    writer = csv.writer(response)
    
    # Header row
    writer.writerow([
        'iso2_code', 'iso3_code', 'name', 'status', 'official_language',
        'currency_name', 'currency_code',
        'numbering_format', 'currency_position', 'date_format', 'decimals', 'archive'
    ])
    
    # Sample data rows
    writer.writerow([
        'US', 'USA', 'United States', 'ACTIVE', 'English',
        'US Dollar', 'USD', 'January', 'December',
        '1,000.00', 'BEFORE', 'MM/DD/YYYY', '2', 'N'
    ])
    writer.writerow([
        'GB', 'GBR', 'United Kingdom', 'ACTIVE', 'English',
        'British Pound', 'GBP', 'April', 'March',
        '1,000.00', 'BEFORE', 'DD/MM/YYYY', '2', 'N'
    ])
    
    return response


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def dashboard_country_map(request):
    """Return ISO2 country codes for the dashboard world map. Restricted to EXEC and ADMIN."""
    try:
        countries = Country.objects.filter(archive="N").values("iso2_code")
        
        country_codes = []
        
        for country in countries:
            iso2 = country.get("iso2_code")
            if iso2:
                country_codes.append(str(iso2).strip().upper())
        
        return JsonResponse({
            "countries": country_codes,
        })
        
    except Exception as e:
        return JsonResponse({
            "countries": [],
            "error": str(e)
        })