from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

from Exactus.country.utils.csv_importer import import_from_csv
from Exactus.country.utils.decorators import role_required
from Exactus.country.models import Country
from Exactus.country.forms import CountryForm, CountryUploadForm
import csv
from django.http import HttpResponse

# ────────────────────────────────────────────────
# 🧩 Helper (Fix)
# ────────────────────────────────────────────────
def is_admin(user):
    """Return True if user is ADMIN based on the main User model."""
    return hasattr(user, "role") and user.role == "ADMIN"


# ────────────────────────────────────────────────
# 🌍 Country Pages
# ────────────────────────────────────────────────

@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def country(request):
    """Show active countries only."""
    countries = Country.objects.filter(archive="N").order_by("name")
    return render(request, "country/index.html", {"countries": countries, "active_countries_count": countries.count(), })


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def country_delete(request):
    """Show archived (deleted) countries only."""
    countries = Country.objects.filter(archive="Y").order_by("name")
    return render(request, "country/delete.html", {"countries": countries})


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def country_create(request):
    """Create a new country."""
    if request.method == "POST":
        form = CountryForm(request.POST)
        if form.is_valid():
            country = form.save()
            messages.success(request, f"{country.name} created successfully.")
            return redirect("country:country")
    else:
        form = CountryForm()

    return render(request, "country/create.html", {"form": form})


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def country_edit(request, slug):
    """Edit a country."""
    country = get_object_or_404(Country, slug=slug)

    if request.method == "POST":
        form = CountryForm(request.POST, instance=country)
        if form.is_valid():
            form.save()
            messages.success(request, f"{country.name} updated successfully.")
            return redirect("country:country")
    else:
        form = CountryForm(instance=country)

    return render(request, "country/edit.html", {"form": form, "country": country, "country_slug": country.slug,})



@staff_member_required
def country_upload_view(request):
    if request.method == "POST":
        form = CountryUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Get dry_run from form if needed
            dry_run = form.cleaned_data.get('dry_run', False)
            
            # Now this matches the function signature in country/utils/csv_importer.py
            result = import_from_csv("country", request.FILES["file"], dry_run=dry_run)
            
            # Store result in session for the result view
            request.session["upload_result"] = result
            
            return redirect("country:country_upload_result")
    else:
        form = CountryUploadForm()

    return render(request, "country/upload_form.html", {"form": form})

@staff_member_required
def country_upload_result_view(request):
    result = request.session.get("upload_result")
    return render(request, "country/upload_result.html", {"result": result})


@staff_member_required
def download_csv_template(request):
    """Download a CSV template for country imports"""
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


def dashboard_country_map(request):
    """Return ISO2 country codes for the dashboard world map."""
    try:
        countries = Country.objects.filter(archive="N").values("iso2_code")
        
        # Debug: Check what data you're getting
        print("Countries queryset:", list(countries))
        
        # Create lists/dicts
        country_codes = []
        country_labels = {}
        
        for country in countries:
            iso2 = country.get("iso2_code")
            
            # Skip if iso2_code is missing or None
            if iso2:
                # Clean and uppercase the ISO2 code
                iso2_clean = str(iso2).strip().upper()
                country_codes.append(iso2_clean)
        
        # Debug: Check what you're returning
        print("Country codes to return:", country_codes)
        
        return JsonResponse({
            "countries": country_codes,
        })
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error in dashboard_country_map: {str(e)}")
        return JsonResponse({
            "countries": [],
            "error": str(e)
        })