
# elements/views.py
import csv
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q 

from Exactus.company import models
from Exactus.elements.models import Element
from Exactus.country.models import Country
from Exactus.elements.forms import ElementForm, ElementUploadForm
from Exactus.elements.utils.csv_importer import import_elements_from_csv
from Exactus.calculationbase.models import CalculationBase
from Exactus.utils.decorators import role_required 


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def element(request, country_slug):
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
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def element_create(request, country_slug):
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
        "elements/create.html",
        {
            "form": form,
            "country": country,
            "country_slug": country_slug,
        },
    )

# elements/views.py (Partial Update)
from Exactus.elements.utils.sync import propagate_element_to_companies

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def element_edit(request, country_slug, element_code):
    country = get_object_or_404(Country, slug=country_slug)
    element = get_object_or_404(Element, country=country, element_code=element_code)
    
    if request.method == "POST":
        form = ElementForm(request.POST, instance=element)
        if form.is_valid():
            # 1. Save the Element changes to the database
            saved_element = form.save()
            
            # 2. Check if the user requested a PD Code Overwrite
            # This 'sync_pdcodes' field comes from the form checkbox we added
            if form.cleaned_data.get('sync_pdcodes'):
                propagate_element_to_companies(saved_element)
                messages.success(request, "Element updated and changes successfully propagated to all linked PD Codes!")
            else:
                messages.success(request, "Element updated locally. PD Codes were NOT changed.")
                
            return redirect("elements:elements", country_slug=country_slug)
    else:
        form = ElementForm(instance=element)

    return render(
        request,
        "elements/edit.html",
        {
            "form": form,
            "element": element,
            "country": country,
            "country_slug": country_slug,
        },
    )


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def element_delete(request, country_slug, element_code):  # Changed from 'pk' to 'element_code'
    country = get_object_or_404(Country, slug=country_slug)
    element = get_object_or_404(Element, element_code=element_code, country=country)
    
    # Check for dependencies in CalculationBase
    # Check if element is used as the main element
    calculation_bases_as_element = CalculationBase.objects.filter(
        element=element
    ).count()
    
    # Check if element is used as element_base (if applicable)
    calculation_bases_as_base = CalculationBase.objects.filter(
        element_base=element
    ).count()
    
    # Total dependencies
    total_dependencies = calculation_bases_as_element + calculation_bases_as_base
    
    # Check if element is referenced in any calculation base
    has_dependencies = total_dependencies > 0

    if request.method == "POST":
        # Block deletion if element has dependencies
        if has_dependencies:
            messages.error(
                request, 
                f"Cannot delete element '{element.element_name}' because "
                f"it is referenced in {total_dependencies} calculation base(s). "
                "Please remove all calculation base references first."
            )
            return redirect("elements:elements", country_slug=country.slug)
        
        # If no dependencies, proceed with deletion
        element_name = element.element_name
        element_code = element.element_code
        element.delete()
        
        messages.success(
            request, 
            f"Element '{element_name}' ({element_code}) deleted successfully."
        )
        return redirect("elements:elements", country_slug=country.slug)

    # Get specific calculation bases for display in template
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
            "calculation_bases_as_element": calculation_bases_as_element,
            "calculation_bases_as_base": calculation_bases_as_base,
        },
    )




@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def element_upload_view(request, country_slug=None):
    """
    Handle element CSV uploads with optional country context.

    - If `country_slug` is provided, all rows are imported for that country.
    - If not, CSV must contain `country_code` (ISO2) for each row.
    """
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    if request.method == "POST":
        form = ElementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]
            dry_run = form.cleaned_data.get("dry_run", False)

            # Read and decode the file content
            try:
                data_set = csv_file.read().decode("utf-8")
            except UnicodeDecodeError:
                csv_file.seek(0)
                data_set = csv_file.read().decode("iso-8859-1")

            io_string = io.StringIO(data_set)

            # Run import
            success_count, error_count, errors = import_elements_from_csv(
                io_string, country=country, dry_run=dry_run
            )

            # Store results in session so the result page can show them
            request.session["upload_results"] = {
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors,
                "country_slug": country_slug,
                "dry_run": dry_run,
            }

            # Redirect to the appropriate result page
            if country_slug:
                return redirect(
                    reverse(
                        "elements:elements_upload_result",
                        kwargs={"country_slug": country_slug},
                    )
                )
            else:
                return redirect(reverse("elements:elements_upload_result_global"))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ElementUploadForm()

    return render(
        request,
        "elements/upload_form.html",
        {
            "form": form,
            "country": country,
            "country_slug": country_slug,
        },
    )


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def element_upload_result_view(request, country_slug=None):
    """
    Display results of a CSV upload.
    """
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    upload_results = request.session.pop("upload_results", None)

    if not upload_results:
        messages.warning(request, "No upload results found. Please upload a file first.")
        if country_slug:
            return redirect(
                reverse(
                    "elements:elements_upload",
                    kwargs={"country_slug": country_slug},
                )
            )
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
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def download_elements_template(request, country_slug=None):
    """
    Download CSV template for elements.
    If `country_slug` is provided, the template will include an example row for that country.
    """
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    response = HttpResponse(content_type="text/csv")

    if country:
        filename = f"elements_template_{country.iso2_code}.csv"
    else:
        filename = "elements_template.csv"

    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    # Header row – must match importer field names
    writer.writerow(
        [
            "country_code",
            "element_code",
            "element_name",
            "element_description",
            "element_status",
            "element_account",
            "element_map_code",
            "element_gl_account",
            "element_frequency",
            "element_type",
            "element_class",
            "element_category",
            "element_taxable",
            "element_tax_flat",
            "element_tax_irregular",
            "element_social_securitable",
            "element_pensionable",
            "element_payable",
            "element_calculate",
            "element_categorytype",
            "archive",
        ]
    )

    # Example row if country is provided
    if country:
        writer.writerow(
            [
                country.iso2_code,  # country_code
                "6000",  # element_code
                "Income Tax",  # element_name
                "Income Tax Description",  # element_description
                "Visible",  # element_status
                "6000",  # element_account
                "6000",  # element_map_code
                "6000",  # element_gl_account
                "Recurring",  # element_frequency
                "Regular",  # element_type
                "Statutory",  # element_class
                "Deduction",  # element_category
                "FALSE",  # element_taxable
                "FALSE",  # element_tax_flat
                "FALSE",  # element_tax_irregular
                "FALSE",  # element_social_securitable
                "FALSE",  # element_pensionable
                "TRUE",  # element_payable
                "TRUE",  # element_calculate
                "Bracketable",  # element_categorytype
                "N",  # archive
            ]
        )

    return response














