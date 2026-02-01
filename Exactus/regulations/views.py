# Exactus/views_regulations.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
import csv

from Exactus.country.utils.decorators import role_required
from Exactus.country.models import Country
from Exactus.regulations.models import Regulations
from Exactus.calculationbase.models import CalculationBase
from Exactus.regulations.forms import RegulationsForm, RegulationsUploadForm
from .utils.csv_importer import import_from_csv


# ────────────────────────────────────────────────────────────────
# LIST REGULATIONS
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def regulations(request, country_slug):
    """List regulations - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    regulations = Regulations.objects.filter(country=country).order_by("-effective_date")
    return render(
        request,
        "regulations/index.html",
        {"country": country, "regulations": regulations, "country_slug": country_slug},
    )


# ────────────────────────────────────────────────────────────────
# CREATE REGULATION
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def regulations_create(request, country_slug):
    """Create a new regulation - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)

    if request.method == "POST":
        form = RegulationsForm(request.POST)
        if form.is_valid():
            regulation = form.save(commit=False)
            regulation.country = country
            regulation.save()
            messages.success(
                request,
                f"Regulation for {country.name} ({regulation.fiscal_year}) created successfully.",
            )
            return redirect("regulations:regulations", country_slug=country.slug)
    else:
        form = RegulationsForm()

    return render(
        request,
        "regulations/create.html",
        {"form": form, "country": country, "country_slug": country_slug},
    )


# ────────────────────────────────────────────────────────────────
# EDIT REGULATION
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def regulations_edit(request, country_slug, regulations_id):
    """Edit an existing regulation - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)

    if request.method == "POST":
        form = RegulationsForm(request.POST, instance=regulations)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Regulation for {country.name} ({regulations.fiscal_year}) updated successfully.",
            )
            return redirect("regulations:regulations", country_slug=country.slug)
    else:
        form = RegulationsForm(instance=regulations)

    return render(
        request,
        "regulations/edit.html",
        {"form": form, "country": country, "regulations": regulations, "country_slug": country_slug},
    )


# ────────────────────────────────────────────────────────────────
# DELETE REGULATION
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def regulations_delete(request, country_slug, regulations_id):
    """Delete a regulation - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)
    
    # Check for dependencies (CalculationBase records)
    calculation_bases_count = regulations.calculation_bases.count()
    has_dependencies = calculation_bases_count > 0

    if request.method == "POST":
        if has_dependencies:
            messages.error(
                request, 
                f"Cannot delete regulation for {country.name} ({regulations.fiscal_year}) because "
                f"it has {calculation_bases_count} calculation base(s) linked to it."
            )
            return redirect("regulations:regulations", country_slug=country.slug)
        
        year = regulations.fiscal_year
        regulations.delete()
        messages.success(request, f"Regulation for {country.name} ({year}) deleted successfully.")
        return redirect("regulations:regulations", country_slug=country.slug)

    return render(
        request,
        "regulations/delete.html",
        {
            "regulations": regulations, 
            "country": country, 
            "country_slug": country_slug,
            "has_dependencies": has_dependencies,
            "calculation_bases_count": calculation_bases_count
        },
    )


# ────────────────────────────────────────────────────────────────
# UPLOAD & TEMPLATE VIEWS (RESTRICTED TO EXEC & ADMIN)
# ────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def regulations_upload_view(request, country_slug=None):
    """Upload regulations via CSV - Restricted to EXEC and ADMIN."""
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    if request.method == "POST":
        form = RegulationsUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            
            try:
                result = import_from_csv("regulations", request.FILES["file"], dry_run=dry_run)
                request.session["upload_result"] = result
                
                if country_slug:
                    return redirect("regulations:regulations_upload_result", country_slug=country_slug)
                else:
                    return redirect("regulations:regulations_upload_result")
                    
            except Exception as e:
                messages.error(request, f"Upload error: {str(e)}")
    else:
        form = RegulationsUploadForm()

    context = {
        "form": form,
        "country": country,
    }
    if country:
        context["country_slug"] = country_slug
        
    return render(request, "regulations/upload_form.html", context)


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def regulations_upload_result_view(request, country_slug=None):
    """View upload results - Restricted to EXEC and ADMIN."""
    result = request.session.get("upload_result", {})
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
    
    context = {
        "result": result,
        "country": country,
    }
    if country:
        context["country_slug"] = country_slug
        
    return render(request, "regulations/upload_result.html", context)


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def download_regulations_template(request, country_slug=None):
    """Download CSV template - Restricted to EXEC and ADMIN."""
    response = HttpResponse(content_type='text/csv')
    filename = "regulations_import_template.csv"
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
        filename = f"regulations_{country.iso2_code}_template.csv"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['country_code', 'fiscal_year', 'effective_date', 'archive'])
    writer.writerow(['US', '2024', '2024-01-01', 'N'])
    writer.writerow(['GB', '2024', '2024-04-06', 'N'])
    writer.writerow(['FR', '2024', '2024-01-01', 'N'])
    
    return response