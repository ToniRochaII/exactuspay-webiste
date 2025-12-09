from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from Exactus.utils.decorators import role_required
from Exactus.company.models import Company
from Exactus.country.models import Country
from Exactus.employee.models import Employee
from .models import PayRegister
from .forms import PayRegisterForm


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def payregister_list(request, country_slug, company_id):
    """List all pay register entries for a company"""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    
    # Get employees for this company
    employees = Employee.objects.filter(company=company)
    
    # Get pay register entries
    payregister_entries = PayRegister.objects.filter(
        employee__company=company
    ).select_related('employee', 'pd_code').order_by('-created_at')
    
    # Calculate totals
    total_amount = payregister_entries.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Group by employee
    entries_by_employee = {}
    for entry in payregister_entries:
        employee_id = entry.employee.id
        if employee_id not in entries_by_employee:
            entries_by_employee[employee_id] = {
                'employee': entry.employee,
                'entries': [],
                'total': 0
            }
        entries_by_employee[employee_id]['entries'].append(entry)
        entries_by_employee[employee_id]['total'] += entry.amount
    
    context = {
        "company": company,
        "country": country,
        "country_slug": country_slug,
        "employees": employees,
        "payregister_entries": payregister_entries,
        "entries_by_employee": entries_by_employee,
        "total_amount": total_amount,
    }
    
    return render(request, "payregister/list.html", context)


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def payregister_create(request, country_slug, company_id):
    """Create a new pay register entry"""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    
    # Get employees for this company for the dropdown
    employees = Employee.objects.filter(company=company)
    
    if request.method == "POST":
        form = PayRegisterForm(request.POST, company=company)
        if form.is_valid():
            payregister = form.save(commit=False)
            payregister.created_by = request.user
            payregister.save()
            messages.success(request, "Pay register entry created successfully.")
            return redirect('payregister:payregister_list', 
                          country_slug=country_slug, 
                          company_id=company_id)
    else:
        form = PayRegisterForm(company=company)
    
    context = {
        "form": form,
        "company": company,
        "country": country,
        "country_slug": country_slug,
        "employees": employees,
    }
    
    return render(request, "payregister/create.html", context)


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def payregister_edit(request, country_slug, company_id, id):
    """Edit a pay register entry"""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    payregister = get_object_or_404(PayRegister, pk=id, employee__company=company)
    
    if request.method == "POST":
        form = PayRegisterForm(request.POST, instance=payregister, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Pay register entry updated successfully.")
            return redirect('payregister:payregister_list', 
                          country_slug=country_slug, 
                          company_id=company_id)
    else:
        form = PayRegisterForm(instance=payregister, company=company)
    
    context = {
        "form": form,
        "payregister": payregister,
        "company": company,
        "country": country,
        "country_slug": country_slug,
    }
    
    return render(request, "payregister/edit.html", context)


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def payregister_delete(request, country_slug, company_id, id):
    """Delete a pay register entry"""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    payregister = get_object_or_404(PayRegister, pk=id, employee__company=company)
    
    if request.method == "POST":
        employee_name = f"{payregister.employee.employee_name} {payregister.employee.employee_surname}"
        payregister.delete()
        messages.success(request, f"Pay register entry for {employee_name} deleted successfully.")
        return redirect('payregister:payregister_list', 
                      country_slug=country_slug, 
                      company_id=company_id)
    
    context = {
        "payregister": payregister,
        "company": company,
        "country": country,
        "country_slug": country_slug,
    }
    
    return render(request, "payregister/delete.html", context)


@login_required
@role_required("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def payregister_by_employee(request, country_slug, company_id, employee_id):
    """View all pay register entries for a specific employee"""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, pk=employee_id, company=company)
    
    payregister_entries = PayRegister.objects.filter(
        employee=employee
    ).select_related('pd_code').order_by('-created_at')
    
    total_amount = payregister_entries.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    context = {
        "employee": employee,
        "company": company,
        "country": country,
        "country_slug": country_slug,
        "payregister_entries": payregister_entries,
        "total_amount": total_amount,
    }
    
    return render(request, "payregister/by_employee.html", context)