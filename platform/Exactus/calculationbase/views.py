# Exactus/calculationbase/views.py

import csv
import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import reverse

from Exactus.country.models import Country
from Exactus.regulations.models import Regulations
from Exactus.elements.models import Element
from Exactus.calculationbase.models import CalculationBase
from Exactus.calculationbase.forms import CalculationBaseForm, CalculationBaseUploadForm
from Exactus.calculationbase.utils.csv_importer import import_calculationbase_from_csv
from Exactus.country.utils.decorators import role_required

# -------------------------------------------------------------------------
# STANDARD CRUD VIEWS
# -------------------------------------------------------------------------

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def calculationbase_list(request, country_slug, regulations_id):
    """List calculation bases - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)

    bases = (
        CalculationBase.objects
        .filter(country=country, regulations=regulations)
        .select_related("element", "element_base")
    )

    return render(
        request,
        "calculationbase/index.html",
        {
            "country": country,
            "regulations": regulations,
            "bases": bases,
            "country_slug": country_slug
        },
    )


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def calculationbase_create(request, country_slug, regulations_id):
    """Create calculation base - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id)

    if request.method == "POST":
        form = CalculationBaseForm(request.POST, country=country, regulations=regulations)
        if form.is_valid():
            cb = form.save(commit=False)
            cb.country = country
            cb.regulations = regulations
            cb.save()
            messages.success(request, "Calculation Base created successfully.")
            return redirect(
                "calculationbase:list",
                country_slug=country.slug,
                regulations_id=regulations.id,
            )
    else:
        # Pre-fill defaults to "Round down" for better UX
        initial_data = {
            'rounding_base': 'Round down',
            'rounding_taxed': 'Round down',
        }
        for i in range(16):
            suffix = f"{i:02d}"
            initial_data[f'round_bracket_logic_{suffix}'] = 'Round down'
            initial_data[f'round_result_logic_{suffix}'] = 'Round down'

        form = CalculationBaseForm(
            country=country, 
            regulations=regulations, 
            initial=initial_data
        )

    bracket_range = [f"{i:02d}" for i in range(16)]

    return render(
        request,
        "calculationbase/form.html",
        {
            "form": form,
            "country": country,
            "regulations": regulations,
            "title": "Add Calculation Base",
            "country_slug": country_slug,
            "bracket_range": bracket_range,
        },
    )


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def calculationbase_edit(request, country_slug, regulations_id, pk):
    """Edit calculation base - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)
    cb = get_object_or_404(CalculationBase, pk=pk, country=country, regulations=regulations)

    if request.method == "POST":
        form = CalculationBaseForm(request.POST, instance=cb, country=country, regulations=regulations)
        if form.is_valid():
            form.save()
            messages.success(request, "Calculation Base updated successfully.")
            return redirect(
                "calculationbase:list",
                country_slug=country.slug,
                regulations_id=regulations.id,
            )
    else:
        form = CalculationBaseForm(instance=cb, country=country, regulations=regulations)

    bracket_range = [f"{i:02d}" for i in range(16)]

    return render(
        request,
        "calculationbase/form.html",
        {
            "form": form,
            "country": country,
            "regulations": regulations,
            "title": "Edit Calculation Base",
            "country_slug": country_slug,
            "bracket_range": bracket_range,
        },
    )


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def calculationbase_delete(request, country_slug, regulations_id, pk):
    """Delete calculation base - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)
    cb = get_object_or_404(CalculationBase, pk=pk, country=country, regulations=regulations)

    if request.method == "POST":
        cb.delete()
        messages.success(request, "Calculation Base deleted successfully.")
        return redirect(
            "calculationbase:list",
            country_slug=country.slug,
            regulations_id=regulations.id,
        )

    return render(
        request,
        "calculationbase/delete.html",
        {
            "cb": cb,
            "country": country,
            "regulations": regulations,
            "country_slug": country_slug
        },
    )


# -------------------------------------------------------------------------
# UPLOAD & TEMPLATE VIEWS (Global / Hybrid / Local)
# -------------------------------------------------------------------------

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def calculationbase_upload(request, country_slug=None, regulations_id=None):
    """Upload calculation bases via CSV - Restricted to EXEC and ADMIN."""
    country = None
    regulations = None

    # 1. Resolve Country Context
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    # 2. Resolve Regulation Context
    if country and regulations_id:
        regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)
        template_name = "calculationbase/upload_form.html"
    elif country:
        template_name = "calculationbase/upload_global.html"
    else:
        template_name = "calculationbase/upload_global.html"

    if request.method == "POST":
        form = CalculationBaseUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]
            dry_run = form.cleaned_data.get("dry_run", False)

            try:
                data_set = csv_file.read().decode("utf-8-sig")
            except UnicodeDecodeError:
                csv_file.seek(0)
                data_set = csv_file.read().decode("iso-8859-1")
            
            io_string = io.StringIO(data_set)

            success_count, error_count, errors = import_calculationbase_from_csv(
                io_string, 
                country=country, 
                regulations=regulations, 
                dry_run=dry_run
            )

            request.session["calc_upload_results"] = {
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors,
                "dry_run": dry_run,
                "country_slug": country_slug,
                "regulations_id": regulations_id
            }

            if country and regulations:
                return redirect(reverse("calculationbase:upload_result", kwargs={
                    "country_slug": country_slug, 
                    "regulations_id": regulations_id
                }))
            elif country:
                return redirect(reverse("calculationbase:upload_result_country_scope", kwargs={
                    "country_slug": country_slug
                }))
            else:
                return redirect("calculationbase:upload_result_global")
    else:
        form = CalculationBaseUploadForm()

    return render(
        request,
        template_name,
        {
            "form": form,
            "country": country,
            "regulations": regulations,
        }
    )


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def calculationbase_upload_result(request, country_slug=None, regulations_id=None):
    """View upload results - Restricted to EXEC and ADMIN."""
    results = request.session.pop("calc_upload_results", None)
    
    country = None
    regulations = None

    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
    
    if country and regulations_id:
        regulations = get_object_or_404(Regulations, pk=regulations_id, country=country)
        template_name = "calculationbase/upload_result.html"
    else:
        template_name = "calculationbase/upload_result_global.html"

    if not results:
        if country and regulations:
            return redirect("calculationbase:list", country_slug=country_slug, regulations_id=regulations_id)
        elif country:
            return redirect("regulations:list", country_slug=country_slug)
        else:
            return redirect("calculationbase:global_tools") 

    return render(
        request,
        template_name,
        {
            "country": country,
            "regulations": regulations,
            "results": results,
        }
    )


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE")
def download_calculationbase_template(request, country_slug=None, regulations_id=None):
    """Download CSV template - Restricted to EXEC and ADMIN."""
    country = None
    regulations = None
    
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
    
    if country and regulations_id:
        regulations = get_object_or_404(Regulations, pk=regulations_id)

    needs_country_col = (country is None)
    needs_year_col = (regulations is None)

    response = HttpResponse(content_type='text/csv')
    
    if country:
        fname = f"calculation_base_template_{country.iso2_code}.csv"
    else:
        fname = "calculation_base_template_GLOBAL.csv"
        
    response['Content-Disposition'] = f'attachment; filename="{fname}"'

    writer = csv.writer(response)

    headers = []
    if needs_country_col:
        headers.append("country_code")
    if needs_year_col:
        headers.append("fiscal_year")

    headers.extend([
        "element_code", "element_base_code", "base_frequency",
        "rounding_base", "rounding_base_decimals",
        "rounding_taxed", "rounding_taxed_decimals"
    ])
    
    for i in range(16):
        s = f"{i:02d}"
        headers.extend([
            f"bracket_{s}", f"rate_{s}", 
            f"round_bracket_logic_{s}", f"round_bracket_dec_{s}",
            f"round_result_logic_{s}", f"round_result_dec_{s}"
        ])

    writer.writerow(headers)

    row = []
    if needs_country_col:
        row.append("AR")
    if needs_year_col:
        row.append("2025")

    row.extend([
        "6000", "", "Monthly",
        "Round down", "2",
        "Round down", "2",
    ])
    
    row.extend(["0.00", "0.050000", "Round down", "2", "Round down", "2"])
    
    for _ in range(15):
        row.extend(["", "", "", "", "", ""])

    writer.writerow(row)

    return response