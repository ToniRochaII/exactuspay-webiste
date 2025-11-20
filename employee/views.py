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
def employee_list(request, pk,company_id):
    country = get_object_or_404(Country, pk=pk)
    company = get_object_or_404(Company, pk=company_id)
    employees = Employee.objects.filter(company=company).order_by("employee_id")
    return render(
        request,
        "employee/list.html",
        {
            "company": company, 
            "employees": employees,
            "country": country,
        },
    )

@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def employee_create(request,  company_id):
    company = get_object_or_404(Company, pk=company_id)

    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.company = company
            employee.save()
            messages.success(request, f"Employee '{employee.employee_name} {employee.employee_surname}' added successfully.")
            return redirect("employee_list", company_id=company.pk)
    else:
        form = EmployeeForm()

    # ✅ Here’s the fix — make sure both `country` and `company` are passed!
    return render(
        request,
        "employee/create.html",
        {
            "form": form,
            "company": company,  # ← this line MUST be present
        },
    )



@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def employee_edit(request, company_id, employee_id):
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, pk=employee_id, company=company)
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Employee '{employee.employee_name} {employee.employee_surname}' updated successfully.")
            return redirect("employee_list", company_id=company.pk)
    else:
        form = EmployeeForm(instance=employee)
    return render(request, "employee/edit.html", {"form": form, "company": company, "employee": employee})


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def employee_delete(request, pk, company_id, employee_id):
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, pk=employee_id, company=company)
    if request.method == "POST":
        employee.delete()
        messages.success(request, f"Employee '{employee.employee_name} {employee.employee_surname}' deleted successfully.")
        return redirect("employee_list", company_id=company.pk)
    return render(request, "employee/delete.html", {"employee": employee, "company": company})






