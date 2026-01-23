# pdcodes/views.py
import csv
import io

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Avg
from django.db import transaction
from django.http import HttpResponse, JsonResponse

from Exactus.pdcodes.utils.decorators import role_required
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
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def pdcode_list(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    
    # FIXED: Added filter to only show 'Visible' pdcodes
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
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def pdcode_create(request, country_slug, company_id):
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
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def pdcode_edit(request, country_slug, company_id, pdcode_code):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    
    # 1. Check if this is a "Protected" code (linked to an Element)
    if is_protected_element(country, pdcode_code):
        # 2. If protected, verify if user has override permissions
        # Only EXEC, ADMIN, COMPLIANCE can edit protected elements in PDcodes
        user_role = getattr(request.user, 'role', '')
        allowed_override_roles = ["EXEC", "ADMIN", "COMPLIANCE"]
        
        if user_role not in allowed_override_roles:
            messages.error(
                request, 
                f"PD Code '{pdcode_code}' is a Country Default Element. "
                "Only EXEC, ADMIN, or COMPLIANCE roles are authorized to edit it here."
            )
            return redirect(
                "pdcodes:pdcodes",
                country_slug=country_slug,
                company_id=company_id,
            )

    # Standard Edit Logic
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
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def pdcode_delete(request, country_slug, company_id, pdcode_code):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    
    # 1. Check if this is a "Protected" code (linked to an Element)
    if is_protected_element(country, pdcode_code):
        # 2. If protected, verify if user has override permissions
        # Only EXEC, ADMIN, COMPLIANCE can delete protected elements in PDcodes
        user_role = getattr(request.user, 'role', '')
        allowed_override_roles = ["EXEC", "ADMIN", "COMPLIANCE"]
        
        if user_role not in allowed_override_roles:
            messages.error(
                request, 
                f"PD Code '{pdcode_code}' is a Country Default Element. "
                "Only EXEC, ADMIN, or COMPLIANCE roles are authorized to delete it."
            )
            return redirect(
                "pdcodes:pdcodes",
                country_slug=country_slug,
                company_id=company_id,
            )

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
@staff_member_required
def pdcode_upload_view(request, country_slug, company_id):
    """
    Upload PD codes via CSV for a specific company
    """
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)

    if request.method == "POST":
        form = PDcodeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            update_existing = form.cleaned_data.get('update_existing', True)
            
            try:
                # Define the field mapping for PD codes
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
                
                # Define required fields
                required_fields = ['pdcode_code', 'pdcode_name']
                
                # Call import function
                result = import_pdcodes_from_csv(
                    file=request.FILES["file"],
                    company=company,
                    field_map=pdcode_field_map,
                    required_fields=required_fields,
                    dry_run=dry_run,
                    update_existing=update_existing
                )
                
                # Store result in session
                request.session["pdcode_upload_result"] = result
                
                # Show appropriate message
                if dry_run:
                    messages.success(request, 
                        f"Dry run completed: {result['created']} to create, {result['updated']} to update. "
                        f"{len(result['errors'])} errors found."
                    )
                else:
                    messages.success(request, 
                        f"Upload completed: {result['created']} created, {result['updated']} updated. "
                        f"{len(result['errors'])} errors."
                    )
                
                # Redirect to result page
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

@staff_member_required
def pdcode_upload_result_view(request, country_slug, company_id):
    """
    Display upload results for PD codes
    """
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    result = request.session.get("pdcode_upload_result", {})
    
    return render(request, "pdcodes/upload_result.html", {
        "result": result,
        "company": company,
        "country": country,
        "country_slug": country_slug
    })

@staff_member_required
def download_pdcodes_template(request, country_slug, company_id):
    """Download a CSV template for PD codes imports"""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="pdcodes_{company.company_code}_template.csv"'
    
    writer = csv.writer(response)
    
    # Header row with all possible fields
    writer.writerow([
        'pdcode_code', 'pdcode_name', 'pdcode_description', 'pdcode_status',
        'pdcode_account', 'pdcode_map_code', 'pdcode_gl_account', 'pdcode_frequency',
        'pdcode_type', 'pdcode_class', 'pdcode_category', 'pdcode_taxable',
        'pdcode_tax_flat', 'pdcode_tax_irregular', 'pdcode_social_securitable',
        'pdcode_pensionable', 'pdcode_payable', 'pdcode_calculate', 'pdcode_categorytype'
    ])
    
    # Sample data
    writer.writerow([
        'BASIC', 'Basic Salary', 'Regular basic salary payment', 'Visible',
        '5001', '1001', '2001', 'Recurring',
        'Regular', 'Standard', 'Payment', 'True',
        'False', 'False', 'True',
        'True', 'True', 'True', 'Base'
    ])
    writer.writerow([
        'BONUS', 'Annual Bonus', 'Year-end performance bonus', 'Visible',
        '5002', '1002', '2002', 'Non-recurring',
        'Irregular', 'Standard', 'Payment', 'True',
        'False', 'True', 'True',
        'True', 'True', 'True', 'Base'
    ])
    writer.writerow([
        'TAX', 'Income Tax', 'Employee income tax deduction', 'Visible',
        '6001', '2001', '3001', 'Recurring',
        'Regular', 'Statutory', 'Deduction', 'False',
        'False', 'False', 'False',
        'False', 'False', 'True', 'Bracketable'
    ])
    writer.writerow([
        'PENSION', 'Pension Contribution', 'Employee pension contribution', 'Visible',
        '6002', '2002', '3002', 'Recurring',
        'Regular', 'Statutory', 'Deduction', 'False',
        'False', 'False', 'True',
        'True', 'False', 'True', 'Pension'
    ])
    
    return response


# ─────────────────────────────────────────
# COUNTRY-WIDE CSV UPLOAD
# ─────────────────────────────────────────
@staff_member_required
def pdcode_upload_country_view(request, country_slug):
    """
    Upload PD codes to ALL companies in a country
    """
    country = get_object_or_404(Country, slug=country_slug)
    
    # Remove is_active filter since it doesn't exist in your Company model
    companies = Company.objects.filter(country=country)
    
    if request.method == "POST":
        form = PDcodeUploadForm(request.POST, request.FILES, country=country)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            update_existing = form.cleaned_data.get('update_existing', True)
            selected_companies = form.cleaned_data.get('company_filter', [])
            
            # Filter companies if specific ones are selected
            if selected_companies:
                companies = companies.filter(company_id__in=selected_companies)
            
            try:
                # Define field mapping
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
                
                # Process upload for all companies
                results = import_pdcodes_to_all_companies(
                    file=request.FILES["file"],
                    companies=companies,
                    field_map=pdcode_field_map,
                    required_fields=required_fields,
                    dry_run=dry_run,
                    update_existing=update_existing
                )
                
                # Store results in session
                request.session["pdcode_country_upload_result"] = results
                
                # Show summary message
                total_created = sum(r['created'] for r in results.values() if isinstance(r, dict))
                total_updated = sum(r['updated'] for r in results.values() if isinstance(r, dict))
                total_errors = sum(len(r['errors']) for r in results.values() if isinstance(r, dict))
                
                if dry_run:
                    messages.success(request, 
                        f"Dry run completed for {len(companies)} companies: "
                        f"{total_created} to create, {total_updated} to update. "
                        f"{total_errors} errors found."
                    )
                else:
                    messages.success(request, 
                        f"Upload completed for {len(companies)} companies: "
                        f"{total_created} created, {total_updated} updated. "
                        f"{total_errors} errors."
                    )
                
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

@staff_member_required
def download_pdcodes_country_template(request, country_slug):
    """Download a CSV template for country-wide PD codes imports"""
    country = get_object_or_404(Country, slug=country_slug)
    
    # Remove is_active filter
    companies = Company.objects.filter(country=country)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="pdcodes_{country.slug}_country_template.csv"'
    
    writer = csv.writer(response)
    
    # Header row with all possible fields
    writer.writerow([
        'pdcode_code', 'pdcode_name', 'pdcode_description', 'pdcode_status',
        'pdcode_account', 'pdcode_map_code', 'pdcode_gl_account', 'pdcode_frequency',
        'pdcode_type', 'pdcode_class', 'pdcode_category', 'pdcode_taxable',
        'pdcode_tax_flat', 'pdcode_tax_irregular', 'pdcode_social_securitable',
        'pdcode_pensionable', 'pdcode_payable', 'pdcode_calculate', 'pdcode_categorytype'
    ])
    
    # Sample data for country-wide template
    writer.writerow([
        'BASIC', 'Basic Salary', 'Regular basic salary payment', 'Visible',
        '5001', '1001', '2001', 'Recurring',
        'Regular', 'Standard', 'Payment', 'True',
        'False', 'False', 'True',
        'True', 'True', 'True', 'Base'
    ])
    writer.writerow([
        'BONUS', 'Annual Bonus', 'Year-end performance bonus', 'Visible',
        '5002', '1002', '2002', 'Non-recurring',
        'Irregular', 'Standard', 'Payment', 'True',
        'False', 'True', 'True',
        'True', 'True', 'True', 'Base'
    ])
    writer.writerow([
        'TAX', 'Income Tax', 'Employee income tax deduction', 'Visible',
        '6001', '2001', '3001', 'Recurring',
        'Regular', 'Statutory', 'Deduction', 'False',
        'False', 'False', 'False',
        'False', 'False', 'True', 'Bracketable'
    ])
    writer.writerow([
        'PENSION', 'Pension Contribution', 'Employee pension contribution', 'Visible',
        '6002', '2002', '3002', 'Recurring',
        'Regular', 'Statutory', 'Deduction', 'False',
        'False', 'False', 'True',
        'True', 'False', 'True', 'Pension'
    ])
    
    return response

@staff_member_required
def pdcode_upload_country_result_view(request, country_slug):
    """
    Display country-wide upload results
    """
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
def country_detail(request, country_slug):
    country = get_object_or_404(Country, slug=country_slug)
    companies = Company.objects.filter(country=country)
    
    # Calculate statistics
    total_pdcodes = PDcode.objects.filter(company__country=country).count()
    employees_count = Employee.objects.filter(company__country=country).count()
    
    # Calculate average PD codes per company
    if companies.exists():
        avg_pdcodes_per_company = PDcode.objects.filter(company__in=companies).count() / companies.count()
        avg_pdcodes_per_company = round(avg_pdcodes_per_company, 1)
    else:
        avg_pdcodes_per_company = 0
    
    # Get recent activity (you might want to create a model for this)
    recent_pdcode_uploads = [
        {
            'date': '2024-01-15',
            'description': 'Bulk PD code upload',
            'status': 'Completed',
            'status_color': 'success'
        },
        # Add more recent activities as needed
    ]
    
    context = {
        'country': country,
        'companies': companies,
        'total_pdcodes': total_pdcodes,
        'employees_count': employees_count,
        'avg_pdcodes_per_company': avg_pdcodes_per_company,
        'recent_uploads': len(recent_pdcode_uploads),
        'recent_pdcode_uploads': recent_pdcode_uploads,
        'last_updated': 'Just now',  # You can make this dynamic
    }
    
    return render(request, 'country/country_detail.html', context)

from Exactus.elements.models import Element

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION")
def pdcode_sync_defaults(request, country_slug, company_id):
    """
    Manually pulls Country Default Elements (1000-4999) into the current Company's PD Codes.
    Useful for new companies or fixing missing defaults.
    """
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, company_id=company_id)
    
    # 1. Fetch all elements for this country
    country_elements = Element.objects.filter(country=country)
    
    synced_count = 0
    
    for element in country_elements:
        try:
            code_val = int(element.element_code)
        except (ValueError, TypeError):
            continue

        # 2. Strict Range Check: Only sync Country Defaults (1000-4999)
        if 1000 <= code_val <= 4999:
            # 3. Create or Update the PD Code locally
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

    if synced_count > 0:
        messages.success(request, f"Successfully synced {synced_count} Country Default codes.")
    else:
        messages.warning(request, "No Country Defaults found to sync.")

    return redirect("pdcodes:pdcodes", country_slug=country_slug, company_id=company_id)