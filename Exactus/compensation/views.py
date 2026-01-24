# Exactus/compensation/views.py
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from django.utils import timezone

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from Exactus.company.models import Company
from Exactus.country.models import Country
from Exactus.employee.models import Employee
from Exactus.utils.decorators import role_required
from Exactus.pdcodes.models import PDcode
from Exactus.compensation.forms import CompensationComponentForm
from Exactus.compensation.models import CompensationComponent
from Exactus.elements.models import Element

ROLES = ("EXEC","ADMIN","COMPLIANCE","BILLING","IMPLEMENTATION","OPERATION",
         "DIRECTOR","MANAGER","SPECIALIST","FINANCE")

@login_required
@role_required(*ROLES)
def compensation_list(request, country_slug, company_id, employee_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    employee = get_object_or_404(Employee, pk=employee_id, company=company)

    # UPDATED: Exclude hidden PD Codes
    active_components = CompensationComponent.objects.filter(
        employee=employee,
        processed=False,
    ).exclude(
        pd_code__pdcode_status="Hidden"
    ).select_related("pd_code")

    # UPDATED: Exclude hidden PD Codes
    archived_components = CompensationComponent.objects.filter(
        employee=employee,
        processed=True,
    ).exclude(
        pd_code__pdcode_status="Hidden"
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
            
            # --- LOGIC: Auto-terminate previous permanent payment ---
            if component.category == "PERMANENT":
                # Find the most recent active permanent component with the same PD Code
                # that started BEFORE this new one.
                previous_comp = CompensationComponent.objects.filter(
                    employee=employee,
                    pd_code=component.pd_code,
                    category="PERMANENT",
                    is_active=True,
                    start_date__lt=component.start_date
                ).order_by('-start_date').first()

                if previous_comp:
                    # Set end date to one day before the new start date
                    previous_comp.end_date = component.start_date - timedelta(days=1)
                    previous_comp.save()
                    messages.info(request, f"Previous {previous_comp.pd_code} record auto-terminated on {previous_comp.end_date}.")
            # --------------------------------------------------------

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
            updated_comp = form.save(commit=False)
            
            # --- LOGIC: Auto-terminate previous permanent payment (on Edit too) ---
            if updated_comp.category == "PERMANENT":
                previous_comp = CompensationComponent.objects.filter(
                    employee=employee,
                    pd_code=updated_comp.pd_code,
                    category="PERMANENT",
                    is_active=True,
                    start_date__lt=updated_comp.start_date
                ).exclude(pk=updated_comp.pk).order_by('-start_date').first()

                if previous_comp:
                    # Update the previous record's end date based on the new start date
                    previous_comp.end_date = updated_comp.start_date - timedelta(days=1)
                    previous_comp.save()
            # ----------------------------------------------------------------------

            updated_comp.save()
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


class EmployeeCompensationListView(LoginRequiredMixin, ListView):
    model = CompensationComponent
    template_name = "payroll/employee_compensation_list.html"
    context_object_name = "earnings"

    def get_queryset(self):
        self.employee = get_object_or_404(Employee, pk=self.kwargs['employee_id'])
        
        # Filter for:
        # 1. This Employee
        # 2. Active Records
        # 3. Only 'Payment' category (Earnings)
        # 4. UPDATED: Exclude Hidden PD Codes
        return CompensationComponent.objects.filter(
            employee=self.employee,
            is_active=True,
            element__element_category='Payment'  # Filters for Earnings only
        ).exclude(
            pd_code__pdcode_status="Hidden"
        ).select_related('element')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        context['company_id'] = self.kwargs.get('company_id')
        context['country_slug'] = self.kwargs.get('country_slug')
        return context


class CompensationListView(LoginRequiredMixin, ListView):
    model = CompensationComponent
    template_name = "compensation/list.html"
    context_object_name = "active_components"

    def get_queryset(self):
        self.company = get_object_or_404(Company, pk=self.kwargs['company_id'])
        self.employee = get_object_or_404(Employee, pk=self.kwargs['employee_id'])
        
        # Return only ACTIVE components for the main list
        # (Assuming active means no end_date OR end_date is in the future)
        today = timezone.now().date()
        
        # UPDATED: Exclude Hidden PD Codes
        return CompensationComponent.objects.filter(
            employee=self.employee,
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).exclude(
            pd_code__pdcode_status="Hidden"
        ).select_related('element').order_by('start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Context for Breadcrumbs and Header
        context['company'] = self.company
        context['country'] = get_object_or_404(Country, slug=self.kwargs['country_slug'])
        context['employee'] = self.employee
        context['country_slug'] = self.kwargs['country_slug']

        # Fetch Archived (Processed/Past) components separately
        today = timezone.now().date()
        
        # UPDATED: Exclude Hidden PD Codes
        context['archived_components'] = CompensationComponent.objects.filter(
            employee=self.employee
        ).filter(
            Q(is_active=False) | Q(end_date__lt=today)
        ).exclude(
            pd_code__pdcode_status="Hidden"
        ).select_related('element').order_by('-end_date')

        return context
    
    # ... existing imports ...
from Exactus.compensation.forms import CompensationUploadForm # Make sure to import the new form
from Exactus.compensation.utils.csv_importer import import_compensation_from_csv
from django.contrib.admin.views.decorators import staff_member_required
import csv 
from django.http import HttpResponse

# ... existing views ...

# ─────────────────────────────────────────
# BULK UPLOAD VIEWS
# ─────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def compensation_upload_view(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)

    if request.method == "POST":
        form = CompensationUploadForm(request.POST, request.FILES)
        if form.is_valid():
            dry_run = form.cleaned_data.get('dry_run', False)
            
            try:
                result = import_compensation_from_csv(
                    file=request.FILES["file"],
                    company=company,
                    dry_run=dry_run
                )
                
                request.session["compensation_upload_result"] = result
                
                if dry_run:
                     messages.info(request, f"Dry Run Complete: {len(result['errors'])} errors found.")
                else:
                     messages.success(request, "Upload processed successfully.")
                
                return redirect("compensation:compensation_upload_result", country_slug=country_slug, company_id=company_id)
                
            except Exception as e:
                messages.error(request, f"Upload failed: {str(e)}")
    else:
        form = CompensationUploadForm()

    return render(request, "compensation/upload_form.html", {
        "form": form,
        "company": company,
        "country": country,
        "country_slug": country_slug
    })

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def compensation_upload_result_view(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    result = request.session.get("compensation_upload_result", {})
    
    return render(request, "compensation/upload_result.html", {
        "result": result,
        "company": company,
        "country": country,
        "country_slug": country_slug
    })

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "BILLING", "IMPLEMENTATION", "OPERATION")
def download_compensation_template(request, country_slug, company_id):
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="earnings_{company.company_code}_template.csv"'
    
    writer = csv.writer(response)
    
    # Headers
    writer.writerow([
        'employee_number', 'pdcode', 'amount', 'start_date', 
        'end_date', 'category', 'frequency', 'reference', 'description'
    ])
    
    # Sample Row
    writer.writerow([
        '1001', 'BASIC', '5000.00', '2024-01-01', 
        '', 'PERMANENT', 'monthly', 'REF001', 'Base Salary Import'
    ])
    
    return response