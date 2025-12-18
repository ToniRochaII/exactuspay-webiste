# Exactus/compensation/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from Exactus.company.models import Company
from Exactus.country.models import Country
from Exactus.employee.models import Employee
from Exactus.utils.decorators import role_required
from Exactus.pdcodes.models import PDcode
from Exactus.compensation.forms import CompensationComponentForm
from Exactus.compensation.models import CompensationComponent


ROLES = ("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION",
         "DIRECTOR","MANAGER","SPECIALIST","FINANCE")
@login_required
@role_required(*ROLES)
def compensation_list(request, country_slug, company_id, employee_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, pk=employee_id, company=company)

    active_components = CompensationComponent.objects.filter(
        employee=employee,
        processed=False,
    ).select_related("pd_code")

    archived_components = CompensationComponent.objects.filter(
        employee=employee,
        processed=True,
    ).select_related("pd_code")

    context = {
        "country": country,
        "company": company,
        "employee": employee,
        "active_components": active_components,
        "archived_components": archived_components,
        "country_slug": country_slug,
    }
    return render(request, "compensation/list.html", context)


@login_required
@role_required(*ROLES)
def compensation_create(request, country_slug, company_id, employee_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, pk=employee_id, company=company)

    if request.method == "POST":
        form = CompensationComponentForm(
            request.POST,
            company=company,
        )
        if form.is_valid():
            component = form.save(commit=False)
            component.employee = employee
            component.created_by = request.user
            component.save()
            messages.success(
                request,
                "Compensation component added successfully."
            )
            return redirect(
                "compensation:compensation_list",
                country_slug=country_slug,
                company_id=company_id,
                employee_id=employee_id,
            )
    else:
        form = CompensationComponentForm(company=company)

    context = {
        "form": form,
        "country": country,
        "company": company,
        "employee": employee,
        "country_slug": country_slug,
        "is_edit": False,
    }
    return render(request, "compensation/form.html", context)


@login_required
@role_required(*ROLES)
@login_required
@role_required(*ROLES)
def compensation_edit(request, country_slug, company_id, employee_id, component_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, pk=employee_id, company=company)
    component = get_object_or_404(
        CompensationComponent,
        pk=component_id,
        employee=employee,
    )

    if request.method == "POST":
        form = CompensationComponentForm(
            request.POST,
            instance=component,
            company=company,
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Compensation component updated successfully."
            )
            return redirect(
                "compensation:compensation_list",
                country_slug=country_slug,
                company_id=company_id,
                employee_id=employee_id,
            )
    else:
        form = CompensationComponentForm(
            instance=component,
            company=company,
        )

    context = {
        "form": form,
        "country": country,
        "company": company,
        "employee": employee,
        "component": component,
        "country_slug": country_slug,
        "is_edit": True,
    }
    return render(request, "compensation/form.html", context)




@login_required
@role_required(*ROLES)
def compensation_delete(request, country_slug, company_id, employee_id, component_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, pk=employee_id, company=company)
    component = get_object_or_404(
        CompensationComponent,
        pk=component_id,
        employee=employee,
    )

    # never allow delete if already processed
    if component.processed:
        messages.error(
            request,
            "This component has already been processed in payroll and cannot be deleted.",
        )
        return redirect(
            "compensation:compensation_list",
            country_slug=country_slug,
            company_id=company_id,
            employee_id=employee_id,
        )

    if request.method == "POST":
        component.delete()
        messages.success(request, "Compensation component deleted successfully.")
        return redirect(
            "compensation:compensation_list",
            country_slug=country_slug,
            company_id=company_id,
            employee_id=employee_id,
        )

    context = {
        "country": country,
        "company": company,
        "employee": employee,
        "component": component,
        "country_slug": country_slug,
    }
    return render(request, "compensation/delete.html", context)













