from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.views import View
from django.db.models import Q
from django.contrib.auth import get_user_model
import csv
import uuid

# Models
from Exactus.company.models import Company
from Exactus.employee.models import Employee
from Exactus.country.models import Country

# Forms
from Exactus.employee.forms import get_employee_form_for_country, EmployeeUploadForm, EmployeeAccessForm

# Utils
from Exactus.utils.decorators import role_required
from Exactus.employee.utils.csv_importer import import_from_csv_with_progress
from Exactus.employee.utils.progress import get_upload_progress

User = get_user_model()

# ────────────────────────────────────────────────
# SECURITY HELPER
# ────────────────────────────────────────────────

def validate_company_access(user, company):
    """
    Verifies if the current user is allowed to access the specific company.
    1. Business Users / Superusers: Access All.
    2. Client Users: Must have access via Client Group or direct assignment.
    """
    # 1. Superusers and Business Roles get full access
    if user.is_superuser or getattr(user, 'is_business_user', False):
        return True

    # 2. Check Client User Access (using the new method we added to User model)
    if hasattr(user, 'get_accessible_companies'):
        accessible_companies = user.get_accessible_companies()
        if company in accessible_companies:
            return True
            
    return False


# ────────────────────────────────────────────────
# EMPLOYEE CRUD
# ────────────────────────────────────────────────

@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def employee_list(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    
    # SECURITY CHECK
    if not validate_company_access(request.user, company):
        messages.error(request, "Access Denied: You do not have permission to view this company.")
        return redirect("dashboard")

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
def employee_create(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)

    # SECURITY CHECK
    if not validate_company_access(request.user, company):
        messages.error(request, "Access Denied: You cannot create employees for this company.")
        return redirect("dashboard")

    FormClass = get_employee_form_for_country(country)

    if request.method == "POST":
        form = FormClass(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.company = company
            employee.save()
            messages.success(request, f"Employee '{employee.employee_name} {employee.employee_surname}' added successfully.")
            return redirect('employee:employee', country_slug=country_slug, company_id=company.company_id)
        else:
            print("FORM ERRORS:", form.errors)
    else:
        form = FormClass()

    return render(
        request,
        "employee/create.html",
        {
            "form": form,
            "company": company,
            "country": country,
            "country_slug": country_slug
        },
    )


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model

# Models
from Exactus.company.models import Company
from Exactus.employee.models import Employee
from Exactus.country.models import Country

# Forms
from Exactus.employee.forms import get_employee_form_for_country, EmployeeAccessForm

# Services & Utils
from Exactus.accounts.services.onboarding import OnboardingService
from Exactus.utils.decorators import role_required

User = get_user_model()

# ────────────────────────────────────────────────
# SECURITY HELPER (Ensure this exists in your file)
# ────────────────────────────────────────────────
def validate_company_access(user, company):
    if user.is_superuser or getattr(user, 'is_business_user', False):
        return True
    if hasattr(user, 'get_accessible_companies'):
        if company in user.get_accessible_companies():
            return True
    return False

# ────────────────────────────────────────────────
# EMPLOYEE EDIT VIEW
# ────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION", "DIRECTOR", "MANAGER", "SPECIALIST", "FINANCE")
def employee_edit(request, country_slug, company_id, employee_id):
    """
    Edit Employee details and manage their System User Account.
    """
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)

    # 1. Security Check
    if not validate_company_access(request.user, company):
        messages.error(request, "Access Denied.")
        return redirect("dashboard")

    employee = get_object_or_404(Employee, pk=employee_id, company=company)

    # 2. Find Linked User (if any)
    linked_user = None
    if employee.email:
        linked_user = User.objects.filter(email=employee.email).first()

    # 3. Get Country-Specific Form
    FormClass = get_employee_form_for_country(country)

    if request.method == "POST":
        
        # ─────────────────────────────────────────────────────────────
        # A. Handle "Create User Account" Action
        # ─────────────────────────────────────────────────────────────
        if "create_user_account" in request.POST:
            # Permission check
            if request.user.role not in ["EXEC", "ADMIN", "DIRECTOR", "MANAGER"]:
                messages.error(request, "You do not have permission to create user accounts.")
            
            # Validation: Email Required
            elif not employee.email:
                messages.error(request, "Cannot create account: Employee has no email address.")
            
            # Validation: Tax ID Required (for Password)
            elif not employee.tax_info_01:
                messages.error(request, "Cannot create account: Tax ID (tax_info_01) is missing. This is required for the initial password.")
                
            # Validation: Account Exists
            elif linked_user:
                messages.warning(request, "User account already exists.")
                
            else:
                try:
                    # Generate unique username from email
                    base_username = employee.email.split('@')[0]
                    username = base_username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1

                    # Execute Onboarding Service
                    # Uses tax_info_01 as the password per requirement
                    new_user = OnboardingService.onboard_employee(
                        username=username,
                        email=employee.email,
                        password=employee.tax_info_01,  
                        role="EMPLOYEE",
                        created_by_user=request.user
                    )
                    
                    messages.success(request, f"User account created for {new_user.username}. Password set to Tax ID.")
                    
                except Exception as e:
                    messages.error(request, f"Error creating user: {str(e)}")
            
            # Redirect to self to refresh state
            return redirect("employee:employee_edit", country_slug=country_slug, company_id=company.company_id, employee_id=employee.id)

        # ─────────────────────────────────────────────────────────────
        # B. Handle Standard Save (Employee Data + Access)
        # ─────────────────────────────────────────────────────────────
        form = FormClass(request.POST, instance=employee)
        
        # Only initialize access form if user exists
        access_form = None
        if linked_user:
            access_form = EmployeeAccessForm(request.POST, instance=linked_user)

        if form.is_valid():
            saved_employee = form.save()
            
            # Handle Access Form (Roles/Client Group)
            if access_form:
                if access_form.is_valid():
                    # Only higher roles can modify permissions
                    if request.user.role in ["EXEC", "ADMIN", "DIRECTOR", "MANAGER"]:
                        access_form.save()
                        
                        # Sync email if changed in employee form
                        if saved_employee.email != linked_user.email:
                            linked_user.email = saved_employee.email
                            linked_user.save()
                            messages.info(request, "Linked user email updated.")
                    else:
                        messages.warning(request, "You do not have permission to modify access roles.")
                else:
                    # If access form has errors, we should probably stop and show them, 
                    # but typically we let the employee save succeed and warn about access.
                    print("ACCESS FORM ERRORS:", access_form.errors)

            messages.success(request, f"Employee '{employee.employee_name}' updated successfully.")
            return redirect("employee:employee", country_slug=country_slug, company_id=company.company_id)
        else:
            print("FORM ERRORS:", form.errors)

    else:
        # GET Request
        form = FormClass(instance=employee)
        access_form = EmployeeAccessForm(instance=linked_user) if linked_user else None

    return render(
        request,
        "employee/edit.html",
        {
            "form": form,
            "access_form": access_form,
            "linked_user": linked_user,
            "employee": employee,
            "company": company,
            "country": country,
            "country_slug": country_slug,
        }
    )

@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def employee_delete(request, country_slug, company_id, employee_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    
    # SECURITY CHECK
    if not validate_company_access(request.user, company):
        messages.error(request, "Access Denied.")
        return redirect("dashboard")

    employee = get_object_or_404(Employee, pk=employee_id, company=company)
    
    if request.method == "POST":
        employee.delete()
        messages.success(request, f"Employee '{employee.employee_name} {employee.employee_surname}' deleted successfully.")
        return redirect('employee:employee', country_slug=country_slug, company_id=company.company_id)
    
    return render(request, "employee/delete.html", {
        "employee": employee, 
        "company": company, 
        "country": country, 
        "country_slug": country_slug
    })


# ────────────────────────────────────────────────
# UPLOAD / IMPORT FUNCTIONALITY
# ────────────────────────────────────────────────

class EmployeeUploadView(View):
    """
    Class-based view for CSV uploads.
    Note: Decorators must be on the dispatch method, NOT the class itself.
    """
    
    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, country_slug, company_id):
        country = get_object_or_404(Country, slug=country_slug)
        company = get_object_or_404(Company, pk=company_id)

        # SECURITY CHECK
        if not validate_company_access(request.user, company):
            messages.error(request, "Access Denied.")
            return redirect("dashboard")

        form = EmployeeUploadForm()

        return render(request, "employee/upload_form.html", {
            "form": form,
            "company": company,
            "country": country,
            "country_slug": country_slug
        })

    def post(self, request, country_slug, company_id):
        country = get_object_or_404(Country, slug=country_slug)
        company = get_object_or_404(Company, pk=company_id)

        # SECURITY CHECK
        if not validate_company_access(request.user, company):
            messages.error(request, "Access Denied.")
            return redirect("dashboard")

        form = EmployeeUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            messages.error(request, "Please correct the errors below.")
            return render(request, "employee/upload_form.html", {
                "form": form,
                "company": company,
                "country": country,
                "country_slug": country_slug
            })

        # Form ok → read dry_run flag
        dry_run = form.cleaned_data.get("dry_run", False)

        # Ensure a progress_id exists
        progress_id = request.POST.get("progress_id") or str(uuid.uuid4())

        try:
            # 1. Base Mapping
            field_map = {
                "company_code": "company",
                "employee_id": "employee_id",
                "employee_number": "employee_number",
                "employee_code": "employee_code",
                "employee_name": "employee_name",
                "employee_surname": "employee_surname",
                "gender": "gender",
                "date_of_birth": "date_of_birth",
                "marital_status": "marital_status",
                "employee_address_type": "employee_address_type",
                "employee_address_01": "employee_address_01",
                "employee_address_02": "employee_address_02",
                "employee_address_03": "employee_address_03",
                "employee_address_04": "employee_address_04",
                "employee_address_05": "employee_address_05",
                "employee_address_06": "employee_address_06",
                "employee_address_07": "employee_address_07",
                "department": "department",
                "cost_centre": "cost_centre",
                "job_title": "job_title",
                "position_number": "position_number",
                "fte": "fte",
                "employment_start_date": "employment_start_date",
                "employment_end_date": "employment_end_date",
            }

            # 2. Dynamic Mapping for 20 Banks and 20 Tax fields
            for i in range(1, 21):
                key_bank = f"bank_{i:02d}"
                field_map[key_bank] = key_bank
                
                key_tax = f"tax_info_{i:02d}"
                field_map[key_tax] = key_tax

            # 3. Execute Import
            required_fields = ["company_code", "employee_number", "employee_name", "employee_surname"]
            
            result = import_from_csv_with_progress(
                file=request.FILES["file"],
                model=Employee,
                field_map=field_map,
                required_fields=required_fields,
                dry_run=dry_run,
                request=request,
                progress_id=progress_id
            )

            request.session["upload_result"] = result

            if dry_run:
                messages.success(
                    request,
                    f"Dry run completed: {result['created']} to create, "
                    f"{result['updated']} to update, {len(result['errors'])} errors."
                )
            else:
                messages.success(
                    request,
                    f"Upload complete: {result['created']} created, "
                    f"{result['updated']} updated, {len(result['errors'])} errors."
                )

            return redirect("employee:employee_upload_result", country_slug=country_slug, company_id=company_id)

        except Exception as e:
            messages.error(request, f"Upload failed: {str(e)}")

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

    # SECURITY CHECK
    if not validate_company_access(request.user, company):
        messages.error(request, "Access Denied.")
        return redirect("dashboard")

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
    
    # SECURITY CHECK
    if not validate_company_access(request.user, company):
        return HttpResponseForbidden("Access Denied")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="employees_{company.company_code}_template.csv"'
    
    writer = csv.writer(response)
    
    # 1. Header row - Includes ALL 20 Bank & Tax fields + Start/End Dates
    headers = [
        'company_code', 'employee_id', 'employee_number', 'employee_code', 'employee_name', 'employee_surname',
        'gender', 'date_of_birth', 'marital_status', 'employee_address_type',
        'employee_address_01', 'employee_address_02', 'employee_address_03', 'employee_address_04', 
        'employee_address_05', 'employee_address_06', 'employee_address_07',
        # Bank 01-20
        'bank_01', 'bank_02', 'bank_03', 'bank_04', 'bank_05', 'bank_06', 'bank_07', 'bank_08', 'bank_09', 'bank_10',
        'bank_11', 'bank_12', 'bank_13', 'bank_14', 'bank_15', 'bank_16', 'bank_17', 'bank_18', 'bank_19', 'bank_20',
        # Job Info
        'department', 'cost_centre', 'job_title', 'position_number', 'fte', 
        'employment_start_date', 'employment_end_date',
        # Tax 01-20
        'tax_info_01', 'tax_info_02', 'tax_info_03', 'tax_info_04', 'tax_info_05', 'tax_info_06', 'tax_info_07',
        'tax_info_08', 'tax_info_09', 'tax_info_10', 'tax_info_11', 'tax_info_12', 'tax_info_13', 'tax_info_14',
        'tax_info_15', 'tax_info_16', 'tax_info_17', 'tax_info_18', 'tax_info_19', 'tax_info_20'
    ]
    writer.writerow(headers)
    
    # 2. Sample data row matching the header columns exactly
    sample_row = [
        company.company_code, 'EMP001', '1001', '1001', 'John', 'Smith',
        'Male', '1985-05-15', 'Married', 'Residential',
        '123 Main Street', 'Apt 4B', 'Downtown', 'New York', 'NY', '10001', 'USA',
        # Bank Samples (01-20)
        'Bank of America', '123456789', 'Checking', '', '', '', '', '', '', '',
        '', '', '', '', '', '', '', '', '', '',
        # Job Samples
        'Sales', 'SALES001', 'Sales Manager', 'POS001', '1.0', '2023-01-01', '',
        # Tax Samples (01-20)
        'AB123456C', '', '1257L', '', '', '', '',
        '', '', '', '', '', '', '',
        '', '', '', '', '', ''
    ]
    writer.writerow(sample_row)
    
    return response


@staff_member_required
def upload_progress(request):
    """
    Endpoint for polling upload progress via JS.
    """
    return get_upload_progress(request)