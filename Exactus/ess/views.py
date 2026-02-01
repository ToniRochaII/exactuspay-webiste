import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.apps import apps
from django.db.models import Sum
from django.http import HttpResponseForbidden
from Exactus.country.utils.decorators import role_required

# Forms
from Exactus.ess.forms import EmployeeSelfServiceForm 

# ──────────────────────────────────────────────────────────────────────────────
# EMPLOYEE SELF-SERVICE (ESS) VIEWS
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "EMPLOYEE")
def employee_self_service(request):
    """
    Employee Self-Service Dashboard.
    Accessible to any logged-in user with a matching Employee record.
    """
    Employee = apps.get_model('employee', 'Employee')
    PayrollResult = apps.get_model('payroll', 'PayrollResult')
    
    # 1. Identity Check
    # Grounds the view context strictly to the authenticated user's profile
    try:
        employee = Employee.objects.get(email=request.user.email)
    except Employee.DoesNotExist:
        return render(request, 'ess/no_record.html', {'user': request.user})

    # 2. Handle Form Submission
    if request.method == "POST":
        # Form allows employees to update specific fields (Address/Bank)
        form = EmployeeSelfServiceForm(request.POST, request.FILES, instance=employee)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been approved and saved.")
            return redirect('ess:dashboard')
        else:
            messages.error(request, "Unable to save. Please check the errors below.")
    else:
        form = EmployeeSelfServiceForm(instance=employee)

    # 3. Data for Charts & History
    historical_results = PayrollResult.objects.filter(
        employee=employee,
        period__status='COMPLETED'
    ).select_related('period').order_by('-period__payment_date').distinct()[:12]

    # Reverse for chronological display in charts
    chart_results = list(historical_results)[::-1]
    
    bar_labels = [res.period.payment_date.strftime('%b %Y') for res in chart_results]
    gross_data = [float(res.gross_pay) for res in chart_results]
    net_data = [float(res.net_pay) for res in chart_results]
    tax_data = [float(res.gross_pay) - float(res.net_pay) for res in chart_results]

    last_payslip = historical_results.first()
    pie_data = []
    if last_payslip:
        current_tax = float(last_payslip.gross_pay) - float(last_payslip.net_pay)
        pie_data = [float(last_payslip.net_pay), current_tax]

    context = {
        'employee': employee,
        'form': form,
        'payslips': historical_results,
        'last_payslip': last_payslip,
        'bar_labels': json.dumps(bar_labels),
        'gross_data': json.dumps(gross_data),
        'net_data': json.dumps(net_data),
        'tax_data': json.dumps(tax_data),
        'pie_data': json.dumps(pie_data),
    }
    return render(request, 'ess/dashboard.html', context)


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "EMPLOYEE")
def view_payslip(request, result_id):
    """
    Detailed Payslip View.
    Includes a security check to ensure employees only see their own data.
    """
    PayrollResult = apps.get_model('payroll', 'PayrollResult')
    
    # Fetch result with related metadata for currency and formatting
    payslip = get_object_or_404(
        PayrollResult.objects.select_related(
            'employee', 
            'period__payroll__company__country'
        ), 
        id=result_id
    )
    
    # SECURITY CHECK:
    # Restricts access so only the owner of the record can view the DEF details.
    # Admins/Execs have system-wide access via the Management views previously processed.
    if payslip.employee.email != request.user.email:
        # Check if user is Admin/Exec to allow privileged viewing if coming from admin panel
        if request.user.role not in ["ADMIN", "EXEC"]:
            return HttpResponseForbidden("You do not have permission to view this payslip.")
    
    return render(request, 'ess/payslip_detail.html', {'payslip': payslip})