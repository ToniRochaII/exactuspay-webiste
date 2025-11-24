from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Company, Employee
from country.models import Country
from .forms import EmployeeForm
from .utils.decorators import role_required

# ────────────────────────────────────────────────
# EMPLOYEE CRUD
# ────────────────────────────────────────────────

@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def employee_list(request, country_slug,company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employees = Employee.objects.filter(company=company).order_by("employee_id")
    return render(
        request,
        "employee/list.html",
        {
            "company": company, 
            "employees": employees,
            "country": country,
            "country_slug": country_slug,
        },
    )

@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def employee_create(request, country_slug,company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)

    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.company = company
            employee.save()
            messages.success(request, f"Employee '{employee.employee_name} {employee.employee_surname}' added successfully.")
            return redirect('employee:employee', country_slug=country_slug, company_id=company.company_id)
    else:
        form = EmployeeForm()

    # ✅ Here’s the fix — make sure both `country` and `company` are passed!
    return render(
        request,
        "employee/create.html",
        {
            "form": form,
            "company": company,
            "country":country  # ← this line MUST be present
            ,"country_slug":country_slug  # ← this line MUST be present
        },
    )



@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def employee_edit(request, country_slug, company_id, employee_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, pk=employee_id, company=company)
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Employee '{employee.employee_name} {employee.employee_surname}' updated successfully.")
            return redirect('employee:employee', country_slug=country_slug, company_id=company.company_id)
    else:
        form = EmployeeForm(instance=employee)
    return render(request, "employee/edit.html", {"form": form, "company": company, "employee": employee, "country": country, "country_slug":country_slug})


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def employee_delete(request, country_slug, company_id, employee_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, pk=employee_id, company=company)
    if request.method == "POST":
        employee.delete()
        messages.success(request, f"Employee '{employee.employee_name} {employee.employee_surname}' deleted successfully.")
        return redirect('employee:employee', country_slug=country_slug, company_id=company.company_id)
    return render(request, "employee/delete.html", {"employee": employee, "company": company, "country": country, "country_slug":country_slug})


# Add these imports at the top of employee/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
import csv
from .utils.csv_importer import import_from_csv
from .forms import EmployeeUploadForm

# Add these views to the existing employee/views.py
@staff_member_required
def employee_upload_view(request, country_slug, company_id):
    """
    Upload employees via CSV for a specific company.
    """
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)

    if request.method == "POST":
        form = EmployeeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            
            try:
                result = import_from_csv("employees", request.FILES["file"], dry_run=dry_run)
                # Store result in session
                request.session["upload_result"] = result
                # Redirect to result page WITH country_slug and company_id
                return redirect("employee:employee_upload_result", country_slug=country_slug, company_id=company_id)
                    
            except Exception as e:
                messages.error(request, f"Upload error: {str(e)}")
    else:
        form = EmployeeUploadForm()

    return render(request, "employee/upload_form.html", {
        "form": form,
        "company": company,
        "country": country,
        "country_slug": country_slug
    })

@staff_member_required
def employee_upload_result_view(request, country_slug, company_id):
    """
    Display upload results for a specific company.
    """
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    result = request.session.get("upload_result", {})
    
    return render(request, "employee/upload_result.html", {
        "result": result,
        "company": company,
        "country": country,
        "country_slug": country_slug
    })

@staff_member_required
def download_employees_template(request, country_slug, company_id):
    """Download a CSV template for employees imports"""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="employees_{company.company_code}_template.csv"'
    
    writer = csv.writer(response)
    
    # Header row
    writer.writerow([
        'company_code', 'employee_id', 'employee_number', 'employee_code', 'employee_name', 'employee_surname',
        'gender', 'date_of_birth', 'marital_status', 'employee_address_type',
        'employee_address_01', 'employee_address_02', 'employee_address_03', 'employee_address_04', 
        'employee_address_05', 'employee_address_06', 'employee_address_07',
        'bank_01', 'bank_02', 'bank_03', 'bank_04', 'bank_05', 'bank_06', 'bank_07', 'bank_08', 'bank_09', 'bank_10',
        'department', 'cost_centre', 'job_title', 'position_number', 'fte',
        'tax_info_01', 'tax_info_02', 'tax_info_03', 'tax_info_04', 'tax_info_05', 'tax_info_06', 'tax_info_07'
    ])
    
    # Sample data for the specific company
    writer.writerow([
        company.company_code, 'EMP001', '1001', '1001', 'John', 'Smith',
        'Male', '1985-05-15', 'Married', 'Residential',
        '123 Main Street', 'Apt 4B', 'Downtown', 'New York', 'NY', '10001', 'USA',
        'Bank of America', '123456789', 'Checking', '', '', '', '', '', '', '',
        'Sales', 'SALES001', 'Sales Manager', 'POS001', '1.0',
        '123-45-6789', '', '', '', '', '', ''
    ])
    writer.writerow([
        company.company_code, 'EMP002', '1002', '1002', 'Maria', 'Garcia',
        'Female', '1990-08-22', 'Single', 'Residential',
        '456 Oak Avenue', '', 'Uptown', 'Los Angeles', 'CA', '90210', 'USA',
        'Chase Bank', '987654321', 'Savings', '', '', '', '', '', '', '',
        'Marketing', 'MKT001', 'Marketing Specialist', 'POS002', '1.0',
        '987-65-4321', '', '', '', '', '', ''
    ])
    
    return response



