import csv
import io
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q 

# Models
from Exactus.elements.models import Element
from Exactus.country.models import Country
from Exactus.calculationbase.models import CalculationBase

# Forms
from Exactus.elements.forms import ElementForm, ElementUploadForm

# Utils & Decorators
from Exactus.country.utils.decorators import role_required 
from Exactus.elements.utils.sync import propagate_element_to_companies
from Exactus.elements.utils.csv_importer import import_elements_from_csv

# ──────────────────────────────────────────────────────────────────────────────
# 1. ELEMENT CRUD VIEWS (RESTRICTED TO EXEC & ADMIN)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN","COMPLIANCE")
def element(request, country_slug):
    """List elements - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    elements = Element.objects.filter(country=country)
    return render(
        request,
        "elements/index.html",
        {
            "elements": elements,
            "country": country,
            "country_slug": country_slug,
        },
    )


@login_required
@role_required("EXEC", "ADMIN","COMPLIANCE")
def element_create(request, country_slug):
    """Create a new element - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    if request.method == "POST":
        form = ElementForm(request.POST)
        if form.is_valid():
            element = form.save(commit=False)
            element.country = country
            element.save()
            messages.success(request, "Element created successfully!")
            return redirect("elements:elements", country_slug=country_slug)
    else:
        form = ElementForm()

    return render(
        request,
        "elements/form.html",
        {
            "form": form,
            "country": country,
            "country_slug": country_slug,
        },
    )


@login_required
@role_required("EXEC", "ADMIN","COMPLIANCE")
def element_edit(request, country_slug, element_code):
    """Edit an existing element - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    element = get_object_or_404(Element, country=country, element_code=element_code)
    
    if request.method == "POST":
        form = ElementForm(request.POST, instance=element)
        if form.is_valid():
            saved_element = form.save()
            
            if form.cleaned_data.get('sync_pdcodes'):
                propagate_element_to_companies(saved_element)
                messages.success(request, f"Element '{saved_element.element_code}' updated and synced!")
            else:
                messages.success(request, f"Element '{saved_element.element_code}' updated locally.")
                
            return redirect("elements:elements", country_slug=country_slug)
    else:
        form = ElementForm(instance=element)

    return render(
        request,
        "elements/form.html",
        {
            "form": form,
            "element": element,
            "country": country,
            "country_slug": country_slug,
        },
    )


@login_required
@role_required("EXEC", "ADMIN","COMPLIANCE")
def element_delete(request, country_slug, element_code):
    """Delete an element - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    element = get_object_or_404(Element, element_code=element_code, country=country)
    
    # Check dependencies in Calculation Bases
    calculation_bases_as_element = CalculationBase.objects.filter(element=element).count()
    calculation_bases_as_base = CalculationBase.objects.filter(element_base=element).count()
    total_dependencies = calculation_bases_as_element + calculation_bases_as_base
    has_dependencies = total_dependencies > 0

    if request.method == "POST":
        if has_dependencies:
            messages.error(
                request, 
                f"Cannot delete element '{element.element_name}' because it is referenced in {total_dependencies} calculation base(s)."
            )
            return redirect("elements:elements", country_slug=country.slug)
        
        element_name = element.element_name
        element_code = element.element_code
        element.delete()
        messages.success(request, f"Element '{element_name}' ({element_code}) deleted successfully.")
        return redirect("elements:elements", country_slug=country.slug)

    calculation_bases = CalculationBase.objects.filter(
        Q(element=element) | Q(element_base=element)
    ).select_related('regulations', 'country').distinct()

    return render(
        request,
        "elements/delete.html",
        {
            "element": element,
            "country": country,
            "country_slug": country_slug,
            "has_dependencies": has_dependencies,
            "total_dependencies": total_dependencies,
            "calculation_bases": calculation_bases,
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# 2. UPLOAD & EXPORT VIEWS (RESTRICTED TO EXEC & ADMIN)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN","COMPLIANCE")
def element_upload_view(request, country_slug=None):
    """Upload elements via CSV - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug) if country_slug else None

    if request.method == "POST":
        form = ElementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]
            dry_run = form.cleaned_data.get("dry_run", False)

            try:
                content = csv_file.read().decode("utf-8-sig")
            except UnicodeDecodeError:
                csv_file.seek(0)
                content = csv_file.read().decode("iso-8859-1")
            
            io_string = io.StringIO(content)

            success_count, error_count, errors = import_elements_from_csv(
                io_string, country=country, dry_run=dry_run
            )

            request.session["upload_results"] = {
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors,
                "country_slug": country_slug,
                "dry_run": dry_run,
            }

            result_url = "elements:elements_upload_result" if country_slug else "elements:elements_upload_result_global"
            kwargs = {"country_slug": country_slug} if country_slug else {}
            return redirect(reverse(result_url, kwargs=kwargs))
    else:
        form = ElementUploadForm()

    return render(request, "elements/upload_form.html", {
        "form": form, 
        "country": country, 
        "country_slug": country_slug,
        "is_global": country is None
    })


@login_required
@role_required("EXEC", "ADMIN","COMPLIANCE")
def element_upload_result_view(request, country_slug=None):
    """View upload results - Restricted to EXEC and ADMIN."""
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    upload_results = request.session.pop("upload_results", None)

    if not upload_results:
        messages.warning(request, "No upload results found.")
        if country_slug:
            return redirect(reverse("elements:elements_upload", kwargs={"country_slug": country_slug}))
        else:
            return redirect(reverse("elements:elements_upload_global"))

    return render(
        request,
        "elements/upload_result.html",
        {
            "success_count": upload_results.get("success_count", 0),
            "error_count": upload_results.get("error_count", 0),
            "errors": upload_results.get("errors", []),
            "dry_run": upload_results.get("dry_run", False),
            "country": country,
            "country_slug": upload_results.get("country_slug"),
        },
    )


@login_required
@role_required("EXEC", "ADMIN","COMPLIANCE")
def download_elements_template(request, country_slug=None):
    """Download CSV template - Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug) if country_slug else None
    
    response = HttpResponse(content_type="text/csv")
    filename = f"elements_template_{country.iso2_code if country else 'GLOBAL'}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    headers = [
        "country_code", "element_code", "element_name", "element_description",
        "element_status", "element_account", "element_map_code", "element_gl_account",
        "element_frequency", "element_type", "element_class", "element_category",
        "element_taxable", "element_tax_flat", "element_tax_irregular",
        "element_social_securitable", "element_pensionable", "element_payable",
        "element_calculate", "element_categorytype", "archive",
    ]
    writer.writerow(headers)

    def write_example(c_code):
        writer.writerow([
            c_code, "1000", "Basic Salary", "Monthly Salary", "Visible", 
            "1000", "1000", "1000", "Recurring", "Regular", "Standard", 
            "Payment", "TRUE", "FALSE", "FALSE", "TRUE", "TRUE", "TRUE", "TRUE", 
            "Prorational", "N"
        ])

    if country:
        write_example(country.iso2_code)
    else:
        demo_codes = ["AR", "CL", "PA", "PE", "AO", "ZA", "NG", "EG", "MA", "SA", "AE", "PK", "IN", "ID", "PH"]
        for code in demo_codes:
            write_example(code)

    return response