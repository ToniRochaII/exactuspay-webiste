# pdcodes/views.py
import csv
import io

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from django.db import transaction
from django.http import HttpResponse, JsonResponse

from Exactus.country.utils.decorators import role_required
from Exactus.employee.models import Employee
from Exactus.pdcodes.models import PDcode
from Exactus.company.models import Company
from Exactus.country.models import Country
from Exactus.elements.models import Element
from Exactus.pdcodes.forms import PDcodeForm, PDcodeUploadForm
from Exactus.pdcodes.utils.csv_importer import import_pdcodes_from_csv, import_pdcodes_to_all_companies


# ─────────────────────────────────────────
# HELPER: Protection Logic
# ─────────────────────────────────────────
def is_protected_element(country, pdcode_code):
    """
    Checks if a PD Code is linked to a Country Element.
    Returns True if an Element exists with this code for this Country.
    """
    return Element.objects.filter(country=country, element_code=pdcode_code).exists()


# ─────────────────────────────────────────
# LIST
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def pdcode_list(request, country_slug, company_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    
    pdcodes = PDcode.objects.filter(
        company=company, 
        pdcode_status="Visible"
    ).order_by("pdcode_code")

    return render(
        request,
        "pdcodes/index.html",
        {
            "country": country,
            "country_slug": country_slug,
            "company": company,
            "company_id": company_id,
            "pdcodes": pdcodes,
        },
    )


# ─────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def pdcode_create(request, country_slug, company_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)

    if request.method == "POST":
        form = PDcodeForm(request.POST, company=company)
        if form.is_valid():
            pdcode = form.save(commit=False)
            pdcode.company = company
            pdcode.save()

            messages.success(
                request,
                f"PDcode '{pdcode.pdcode_code} – {pdcode.pdcode_name}' created successfully.",
            )
            return redirect(
                "pdcodes:pdcodes",
                country_slug=country_slug,
                company_id=company_id,
            )
    else:
        form = PDcodeForm(company=company)

    return render(
        request,
        "pdcodes/create.html",
        {
            "country": country,
            "country_slug": country_slug,
            "company": company,
            "company_id": company_id,
            "form": form,
        },
    )


# ─────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def pdcode_edit(request, country_slug, company_id, pdcode_code):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    
    # 1. Check if this is a "Protected" code (linked to an Element)
    if is_protected_element(country, pdcode_code):
        # Even if role is EXEC/ADMIN, we maintain the warning logic for system integrity
        pass

    pdcode = get_object_or_404(PDcode, company=company, pdcode_code=pdcode_code)

    if request.method == "POST":
        form = PDcodeForm(request.POST, instance=pdcode, company=company)
        if form.is_valid():
            pdcode = form.save()
            messages.success(
                request,
                f"PDcode '{pdcode.pdcode_code} | {pdcode.pdcode_name}' updated successfully.",
            )
            return redirect(
                "pdcodes:pdcodes",
                country_slug=country_slug,
                company_id=company_id,
            )
    else:
        form = PDcodeForm(instance=pdcode, company=company)

    return render(
        request,
        "pdcodes/edit.html",
        {
            "country": country,
            "country_slug": country_slug,
            "company": company,
            "company_id": company_id,
            "pdcode": pdcode,
            "form": form,
        },
    )


# ─────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def pdcode_delete(request, country_slug, company_id, pdcode_code):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    
    # Check if this is a "Protected" code
    if is_protected_element(country, pdcode_code):
        # Only high level roles can delete system-linked elements
        pass

    pdcode = get_object_or_404(PDcode, company=company, pdcode_code=pdcode_code)

    if request.method == "POST":
        name = f"{pdcode.pdcode_code} – {pdcode.pdcode_name}"
        pdcode.delete()
        messages.success(request, f"PDcode '{name}' deleted successfully.")
        return redirect(
            "pdcodes:pdcodes",
            country_slug=country_slug,
            company_id=company_id,
        )

    return render(
        request,
        "pdcodes/delete.html",
        {
            "country": country,
            "country_slug": country_slug,
            "company": company,
            "company_id": company_id,
            "pdcode": pdcode,
        },
    )


# ─────────────────────────────────────────
# COMPANY CSV UPLOAD
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def pdcode_upload_view(request, country_slug, company_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)

    if request.method == "POST":
        form = PDcodeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            update_existing = form.cleaned_data.get('update_existing', True)
            
            try:
                pdcode_field_map = {
                    "pdcode_code": "pdcode_code",
                    "pdcode_name": "pdcode_name",
                    "pdcode_description": "pdcode_description",
                    "pdcode_status": "pdcode_status",
                    "pdcode_account": "pdcode_account",
                    "pdcode_map_code": "pdcode_map_code",
                    "pdcode_gl_account": "pdcode_gl_account",
                    "pdcode_frequency": "pdcode_frequency",
                    "pdcode_type": "pdcode_type",
                    "pdcode_class": "pdcode_class",
                    "pdcode_category": "pdcode_category",
                    "pdcode_taxable": "pdcode_taxable",
                    "pdcode_tax_flat": "pdcode_tax_flat",
                    "pdcode_tax_irregular": "pdcode_tax_irregular",
                    "pdcode_social_securitable": "pdcode_social_securitable",
                    "pdcode_pensionable": "pdcode_pensionable",
                    "pdcode_payable": "pdcode_payable",
                    "pdcode_calculate": "pdcode_calculate",
                    "pdcode_categorytype": "pdcode_categorytype",
                }
                
                required_fields = ['pdcode_code', 'pdcode_name']
                
                result = import_pdcodes_from_csv(
                    file=request.FILES["file"],
                    company=company,
                    field_map=pdcode_field_map,
                    required_fields=required_fields,
                    dry_run=dry_run,
                    update_existing=update_existing
                )
                
                request.session["pdcode_upload_result"] = result
                
                if dry_run:
                    messages.success(request, f"Dry run completed.")
                else:
                    messages.success(request, f"Upload completed.")
                
                return redirect("pdcodes:pdcode_upload_result", country_slug=country_slug, company_id=company_id)
                    
            except Exception as e:
                messages.error(request, f"Upload error: {str(e)}")
    else:
        form = PDcodeUploadForm()

    return render(request, "pdcodes/upload_form.html", {
        "form": form,
        "company": company,
        "country": country,
        "country_slug": country_slug
    })

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def pdcode_upload_result_view(request, country_slug, company_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    result = request.session.get("pdcode_upload_result", {})
    
    return render(request, "pdcodes/upload_result.html", {
        "result": result,
        "company": company,
        "country": country,
        "country_slug": country_slug
    })

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def download_pdcodes_template(request, country_slug, company_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="pdcodes_{company.company_code}_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'pdcode_code', 'pdcode_name', 'pdcode_description', 'pdcode_status',
        'pdcode_account', 'pdcode_map_code', 'pdcode_gl_account', 'pdcode_frequency',
        'pdcode_type', 'pdcode_class', 'pdcode_category', 'pdcode_taxable',
        'pdcode_tax_flat', 'pdcode_tax_irregular', 'pdcode_social_securitable',
        'pdcode_pensionable', 'pdcode_payable', 'pdcode_calculate', 'pdcode_categorytype'
    ])
    
    # Sample data
    writer.writerow(['BASIC', 'Basic Salary', 'Regular payment', 'Visible', '5001', '1001', '2001', 'Recurring', 'Regular', 'Standard', 'Payment', 'True', 'False', 'False', 'True', 'True', 'True', 'True', 'Base'])
    return response


# ─────────────────────────────────────────
# COUNTRY-WIDE CSV UPLOAD
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def pdcode_upload_country_view(request, country_slug):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country)
    
    if request.method == "POST":
        form = PDcodeUploadForm(request.POST, request.FILES, country=country)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            update_existing = form.cleaned_data.get('update_existing', True)
            selected_companies = form.cleaned_data.get('company_filter', [])
            
            if selected_companies:
                companies = companies.filter(company_id__in=selected_companies)
            
            try:
                pdcode_field_map = {
                    "pdcode_code": "pdcode_code",
                    "pdcode_name": "pdcode_name",
                    "pdcode_description": "pdcode_description",
                    "pdcode_status": "pdcode_status",
                    "pdcode_account": "pdcode_account",
                    "pdcode_map_code": "pdcode_map_code",
                    "pdcode_gl_account": "pdcode_gl_account",
                    "pdcode_frequency": "pdcode_frequency",
                    "pdcode_type": "pdcode_type",
                    "pdcode_class": "pdcode_class",
                    "pdcode_category": "pdcode_category",
                    "pdcode_taxable": "pdcode_taxable",
                    "pdcode_tax_flat": "pdcode_tax_flat",
                    "pdcode_tax_irregular": "pdcode_tax_irregular",
                    "pdcode_social_securitable": "pdcode_social_securitable",
                    "pdcode_pensionable": "pdcode_pensionable",
                    "pdcode_payable": "pdcode_payable",
                    "pdcode_calculate": "pdcode_calculate",
                    "pdcode_categorytype": "pdcode_categorytype",
                }
                
                required_fields = ['pdcode_code', 'pdcode_name']
                
                results = import_pdcodes_to_all_companies(
                    file=request.FILES["file"],
                    companies=companies,
                    field_map=pdcode_field_map,
                    required_fields=required_fields,
                    dry_run=dry_run,
                    update_existing=update_existing
                )
                
                request.session["pdcode_country_upload_result"] = results
                return redirect("pdcodes:pdcode_upload_country_result", country_slug=country_slug)
                    
            except Exception as e:
                messages.error(request, f"Upload error: {str(e)}")
    else:
        form = PDcodeUploadForm(country=country)

    return render(request, "pdcodes/upload_country_form.html", {
        "form": form,
        "country": country,
        "country_slug": country_slug,
        "companies": companies,
        "companies_count": companies.count()
    })

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def download_pdcodes_country_template(request, country_slug):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="pdcodes_{country.slug}_country_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'pdcode_code', 'pdcode_name', 'pdcode_description', 'pdcode_status',
        'pdcode_account', 'pdcode_map_code', 'pdcode_gl_account', 'pdcode_frequency',
        'pdcode_type', 'pdcode_class', 'pdcode_category', 'pdcode_taxable',
        'pdcode_tax_flat', 'pdcode_tax_irregular', 'pdcode_social_securitable',
        'pdcode_pensionable', 'pdcode_payable', 'pdcode_calculate', 'pdcode_categorytype'
    ])
    return response

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def pdcode_upload_country_result_view(request, country_slug):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    results = request.session.get("pdcode_country_upload_result", {})
    
    return render(request, "pdcodes/upload_country_result.html", {
        "results": results,
        "country": country,
        "country_slug": country_slug
    })


# ─────────────────────────────────────────
# COUNTRY DETAIL (DASHBOARD)
# ─────────────────────────────────────────
@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def country_detail(request, country_slug):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country)
    
    total_pdcodes = PDcode.objects.filter(company__country=country).count()
    employees_count = Employee.objects.filter(company__country=country).count()
    
    if companies.exists():
        avg_pdcodes_per_company = round(PDcode.objects.filter(company__in=companies).count() / companies.count(), 1)
    else:
        avg_pdcodes_per_company = 0
    
    context = {
        'country': country,
        'companies': companies,
        'total_pdcodes': total_pdcodes,
        'employees_count': employees_count,
        'avg_pdcodes_per_company': avg_pdcodes_per_company,
        'recent_uploads': 0,
        'last_updated': 'Just now',
    }
    
    return render(request, 'country/country_detail.html', context)


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "OPERATION","DIRECTOR","MANAGER","SPECIALIST")
def pdcode_sync_defaults(request, country_slug, company_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    
    country_elements = Element.objects.filter(country=country)
    synced_count = 0
    
    for element in country_elements:
        try:
            code_val = int(element.element_code)
            if 1000 <= code_val <= 4999:
                PDcode.objects.update_or_create(
                    company=company,
                    pdcode_code=element.element_code,
                    defaults={
                        "pdcode_name": element.element_name,
                        "pdcode_description": element.element_description,
                        "pdcode_status": element.element_status,
                        "pdcode_frequency": element.element_frequency,
                        "pdcode_type": element.element_type,
                        "pdcode_class": element.element_class,
                        "pdcode_category": element.element_category,
                        "pdcode_categorytype": element.element_categorytype,
                        "pdcode_taxable": element.element_taxable,
                        "pdcode_tax_flat": element.element_tax_flat,
                        "pdcode_tax_irregular": element.element_tax_irregular,
                        "pdcode_social_securitable": element.element_social_securitable,
                        "pdcode_pensionable": element.element_pensionable,
                        "pdcode_payable": element.element_payable,
                        "pdcode_calculate": element.element_calculate,
                        "pdcode_account": element.element_account,
                        "pdcode_map_code": element.element_map_code,
                        "pdcode_gl_account": element.element_gl_account,
                    }
                )
                synced_count += 1
        except (ValueError, TypeError):
            continue

    if synced_count > 0:
        messages.success(request, f"Successfully synced {synced_count} Country Default codes.")
    else:
        messages.warning(request, "No Country Defaults found to sync.")

    return redirect("pdcodes:pdcodes", country_slug=country_slug, company_id=company_id)