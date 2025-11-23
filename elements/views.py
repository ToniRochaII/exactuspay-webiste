from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .utils.decorators import role_required
from .models import Country, Element
from .forms import ElementForm


# ────────────────────────────────────────────────────────────────
# LIST ELEMENTS
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def element(request, country_slug):
    """
    List all elements for a specific country.
    """
    country = get_object_or_404(Country, slug=country_slug)
    elements = Element.objects.filter(country=country).order_by("element_code")
    return render(
        request,
        "elements/index.html",
        {"country": country, "elements": elements, "country_slug":country_slug},
    )

# ────────────────────────────────────────────────────────────────
# CREATE ELEMENT
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def element_create(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)

    form = ElementForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        element = form.save(commit=False)
        element.country = country
        element.save()

        messages.success(
            request,
            f"Element '{element.element_code} – {element.element_name}' created successfully."
        )
        return redirect("elements:elements", country_slug=country.slug)

    return render(
        request,
        "elements/create.html",
        {
            "form": form,
            "country": country,
            "country_slug": country_slug,
        },
    )



# ────────────────────────────────────────────────────────────────
# EDIT ELEMENT
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def element_edit(request, country_slug, element_code):
    """
    Edit an existing element.
    """
    country = get_object_or_404(Country, slug=country_slug)
    element = get_object_or_404(Element, element_code=element_code, country=country)

    if request.method == "POST":
        form = ElementForm(request.POST, instance=element)
        if form.is_valid():
            form.save()
            messages.success(request, f"Element '{element.element_code} | {element.element_name}' updated successfully.")
            return redirect("elements:elements", country_slug=country.slug)
    else:
        form = ElementForm(instance=element)

    return render(
        request,
        "elements/edit.html",
        {"form": form, "country": country, "element": element, "country_slug":country_slug},
    )


# ────────────────────────────────────────────────────────────────
# DELETE ELEMENT
# ────────────────────────────────────────────────────────────────
@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION")
def element_delete(request, country_slug, element_code):
    """
    Edit an existing element.
    """
    country = get_object_or_404(Country, slug=country_slug)
    element = get_object_or_404(Element, element_code=element_code, country=country)

    if request.method == "POST":
        name = element.element_name
        element.delete()
        messages.success(request, f"Element '{element_code}' deleted successfully.")
        return redirect("elements:elements", country_slug=country.slug)

    return render(
        request,
        "elements/delete.html",
        {"element": element, "country": country, "country_slug":country_slug},
    )


# Add these imports at the top of elements/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
import csv
from .utils.csv_importer import import_from_csv
from .forms import ElementUploadForm

# Add these views to the existing elements/views.py
@staff_member_required
def element_upload_view(request, country_slug=None):
    """
    Upload elements via CSV. Can be country-specific or global.
    """
    country = None
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)

    if request.method == "POST":
        form = ElementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            
            try:
                result = import_from_csv("elements", request.FILES["file"], dry_run=dry_run)
                request.session["upload_result"] = result
                
                if country_slug:
                    return redirect("elements:elements_upload_result", country_slug=country_slug)
                else:
                    return redirect("elements:elements_upload_result")
                    
            except Exception as e:
                messages.error(request, f"Upload error: {str(e)}")
    else:
        form = ElementUploadForm()

    context = {
        "form": form,
        "country": country,
    }
    if country:
        context["country_slug"] = country_slug
        
    return render(request, "elements/upload_form.html", context)

@staff_member_required
def element_upload_result_view(request, country_slug=None):
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
    }
    if country:
        context["country_slug"] = country_slug
        
    return render(request, "elements/upload_result.html", context)

@staff_member_required
def download_elements_template(request, country_slug=None):
    """Download a CSV template for elements imports"""
    response = HttpResponse(content_type='text/csv')
    filename = "elements_import_template.csv"
    if country_slug:
        country = get_object_or_404(Country, slug=country_slug)
        filename = f"elements_{country.iso2_code}_template.csv"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Header row
    writer.writerow([
        'country_code', 'element_code', 'element_name', 'element_description',
        'element_status', 'element_account', 'element_map_code', 'element_gl_account',
        'element_frequency', 'element_type', 'element_class', 'element_category',
        'element_taxable', 'element_tax_flat', 'element_tax_irregular',
        'element_social_securitable', 'element_pensionable', 'element_payable',
        'element_calculate', 'element_categorytype', 'archive'
    ])
    
    # Sample data rows
    writer.writerow([
        'US', 'BASIC', 'Basic Salary', 'Employee basic salary',
        'Visible', '5001', '1001', '2001', 'Recurring', 'Regular', 'Standard', 'Payment',
        'TRUE', 'FALSE', 'FALSE', 'TRUE', 'TRUE', 'TRUE', 'TRUE', 'Base', 'N'
    ])
    writer.writerow([
        'US', 'TAX', 'Income Tax', 'Employee income tax deduction',
        'Visible', '5002', '1002', '2002', 'Recurring', 'Regular', 'Statutory', 'Deduction',
        'FALSE', 'FALSE', 'FALSE', 'FALSE', 'FALSE', 'FALSE', 'TRUE', 'Bracketable', 'N'
    ])
    
    return response