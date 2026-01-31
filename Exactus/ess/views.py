import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.apps import apps
from django.db.models import Sum
from Exactus.employee.forms.base_employee_form import BaseEmployeeForm

@login_required
def employee_self_service(request):
    """
    Employee Self-Service Dashboard.
    Updated to include Tax/Deduction data for the bar chart.
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
        form = BaseEmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been updated.")
            return redirect('ess:dashboard')
        else:
            messages.error(request, "Please check the details you entered.")
    else:
        form = BaseEmployeeForm(instance=employee)

    # 3. Data for Charts & History
    # Fetch last 12 completed payslips
    historical_results = PayrollResult.objects.filter(
        employee=employee,
        period__status='COMPLETED'
    ).select_related('period').order_by('-period__payment_date').distinct()[:12]

    # Reverse list to show oldest -> newest on the chart
    chart_results = list(historical_results)[::-1]
    
    # Prepare Lists
    bar_labels = [res.period.payment_date.strftime('%b %Y') for res in chart_results]
    gross_data = [float(res.gross_pay) for res in chart_results]
    net_data = [float(res.net_pay) for res in chart_results]
    
    # Calculate Deductions (Gross - Net) for the new bar
    tax_data = [float(res.gross_pay) - float(res.net_pay) for res in chart_results]

    # Pie Chart Data (Last Pay Breakdown)
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
        # JSON Data for Charts
        'bar_labels': json.dumps(bar_labels),
        'gross_data': json.dumps(gross_data),
        'net_data': json.dumps(net_data),
        'tax_data': json.dumps(tax_data),  # <--- Added this line
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