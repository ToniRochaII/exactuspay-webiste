import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.apps import apps
from django.db.models import Sum
from Exactus.employee.forms.base_employee_form import BaseEmployeeForm

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.apps import apps
from django.db.models import Sum

# IMPORT THE NEW FORM HERE
from Exactus.ess.forms import EmployeeSelfServiceForm 

@login_required
def employee_self_service(request):
    """
    Employee Self-Service Dashboard.
    """
    Employee = apps.get_model('employee', 'Employee')
    PayrollResult = apps.get_model('payroll', 'PayrollResult')
    
    # 1. Identity Check
    try:
        employee = Employee.objects.get(email=request.user.email)
    except Employee.DoesNotExist:
        return render(request, 'ess/no_record.html', {'user': request.user})

    # 2. Handle Form Submission
    if request.method == "POST":
        # Use EmployeeSelfServiceForm here
        form = EmployeeSelfServiceForm(request.POST, request.FILES, instance=employee)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been approved and saved.")
            return redirect('ess:dashboard')
        else:
            # This will now only show errors relevant to Address/Bank fields
            messages.error(request, "Unable to save. Please check the errors below.")
            print(form.errors) # Debugging
    else:
        # Use EmployeeSelfServiceForm here
        form = EmployeeSelfServiceForm(instance=employee)

    # 3. Data for Charts & History (Existing code remains same)
    historical_results = PayrollResult.objects.filter(
        employee=employee,
        period__status='COMPLETED'
    ).select_related('period').order_by('-period__payment_date').distinct()[:12]

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
def view_payslip(request, result_id):
    PayrollResult = apps.get_model('payroll', 'PayrollResult')
    # Use select_related to get the company and country for the currency symbol/names
    payslip = get_object_or_404(
        PayrollResult.objects.select_related('employee', 'period__payroll__company__country'), 
        id=result_id
    )
    
    # Security check: Ensure the employee email matches the logged-in user email
    if payslip.employee.email != request.user.email:
        return HttpResponseForbidden("You do not have permission to view this payslip.")
    
    return render(request, 'ess/payslip_detail.html', {'payslip': payslip})