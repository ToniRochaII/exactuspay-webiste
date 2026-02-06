import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.apps import apps
from django.db.models import Sum
from django.http import HttpResponseForbidden
from Exactus.country.utils.decorators import role_required

# Forms
from Exactus.ess.forms import EmployeeSelfServiceForm 
from Exactus.company.models import Company
from Exactus.employee.models import Employee
from Exactus.payroll.models import PayrollResult

# ──────────────────────────────────────────────────────────────────────────────
# EMPLOYEE SELF-SERVICE (ESS) VIEWS
# ──────────────────────────────────────────────────────────────────────────────

# ... (Imports remain the same)

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "EMPLOYEE")
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

    # ... (Form handling remains the same) ...
    if request.method == "POST":
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

    chart_results = list(historical_results)[::-1]
    bar_labels = [res.period.payment_date.strftime('%b %Y') for res in chart_results]
    
    # --- PREPARE DETAILED DATA ---
    detailed_chart_data = []
    found_codes = set()

    for res in chart_results:
        details = {}
        if isinstance(res.details, dict):
            details = res.details
        elif isinstance(res.details, str) and res.details.strip():
            try: details = json.loads(res.details)
            except: details = {}
        
        detailed_chart_data.append(details)
        found_codes.update(details.keys())
    
    # --- NEW: BUILD CODE -> NAME MAPPING ---
    # We fetch descriptions for every code found in the payroll results
    code_map = {
        '5000': 'Gross Pay',
        '6000': 'PAYE Tax',
        '7000': 'National Insurance',
        '8000': 'Net Pay'
    }

    # 1. Fetch Company PDCodes (e.g., Bonuses, Commission)
    try:
        PDCodeModel = apps.get_model('pdcodes', 'PDCode')
        # Filter strictly by the codes we actually found to save DB hits
        company_codes = PDCodeModel.objects.filter(
            company=employee.company, 
            pdcode_code__in=found_codes
        )
        for pd in company_codes:
            code_map[str(pd.pdcode_code)] = pd.pdcode_description
    except LookupError: pass

    # 2. Fetch Global Elements (e.g., Tax, NI, Statutory Pay)
    try:
        ElementModel = apps.get_model('elements', 'Element')
        global_elements = ElementModel.objects.filter(
            country=employee.company.country,
            element_code__in=found_codes
        )
        for el in global_elements:
            code_map[str(el.element_code)] = el.element_description
    except LookupError: pass
    # ---------------------------------------

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
        'chart_details_json': json.dumps(detailed_chart_data), 
        'pie_data': json.dumps(pie_data),
        
        # Pass the map to the template
        'code_map_json': json.dumps(code_map), 
    }
    return render(request, 'ess/dashboard.html', context)





@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE", "IMPLEMENTATION", "EMPLOYEE")
def view_payslip(request, result_id):
    """
    Detailed Payslip View.
    """
    PayrollResult = apps.get_model('payroll', 'PayrollResult')
    
    # 1. Fetch Result
    result = get_object_or_404(
        PayrollResult.objects.select_related(
            'employee', 
            'period__payroll__company__country'
        ), 
        id=result_id
    )
    
    # 2. Security Check
    if result.employee.email != request.user.email:
        if request.user.role not in ["ADMIN", "EXEC"]:
            return HttpResponseForbidden("Access Denied")

    # 3. Setup Metadata
    company = result.period.payroll.company
    country = result.period.payroll.company.country
    code_meta = {} 
    
    try:
        ElementModel = apps.get_model('elements', 'Element')
        elements = ElementModel.objects.filter(country=country)
        for e in elements:
            code_meta[str(e.element_code)] = {'status': e.element_status, 'desc': e.element_description}
    except LookupError: pass

    try:
        PDCodeModel = apps.get_model('pdcodes', 'PDCode')
        pdcodes = PDCodeModel.objects.filter(company=company)
        for p in pdcodes:
            code_meta[str(p.pdcode_code)] = {'status': p.pdcode_status, 'desc': p.pdcode_description}
    except LookupError: pass

    # 4. Process Details
    if isinstance(result.details, dict):
        details = result.details
    elif isinstance(result.details, str):
        try: details = json.loads(result.details)
        except: details = {}
    else:
        details = {}

    payments = []
    deductions = []
    
    running_total_pay = 0.0
    running_total_ded = 0.0
    net_pay = 0.0

    for code, val_str in details.items():
        try: val = float(val_str)
        except: val = 0.0
        
        if abs(val) < 0.01: continue 

        if str(code) == '8000': 
            net_pay = val
            continue 

        meta = code_meta.get(str(code))
        
        if meta:
            status = meta['status']
            desc = meta['desc']
        else:
            status = 'Visible'
            desc = f"Code {code}"

        if status != 'Visible': continue

        try: code_int = int(code)
        except: continue

        if 1000 <= code_int <= 4999:
            payments.append({'desc': desc, 'val': val})
            running_total_pay += val

        elif 6000 <= code_int <= 9999:
            deductions.append({'desc': desc, 'val': abs(val)})
            running_total_ded += abs(val)

    # 5. Construct Context
    address = getattr(result.employee, 'address_line_1', 
              getattr(result.employee, 'address_1', ''))

    payslip_data = {
        'employee': {
            'name': f"{result.employee.employee_name} {result.employee.employee_surname}",
            'id': str(result.employee.employee_code),
            'ni_number': result.employee.tax_info_01,  
            'ni_category': result.employee.tax_info_04,
            'tax_code': result.employee.tax_info_03,
            'dept': result.employee.department,
            'address': address
        },
        'payments': payments,
        'deductions': deductions,
        'totals': {
            'payments': running_total_pay,
            'deductions': running_total_ded,
            'net': net_pay
        },
        'period': {
            'date': result.period.payment_date,
            'tax_period': result.period.period_number,
            'start_date': result.period.start_date,
            'end_date': result.period.end_date
        },
        'company': company
    }
    
    # Wrap in list
    context = {
        'company': company,
        'payslips': [payslip_data] 
    }
    
    return render(request, 'ess/payslip_detail.html', context)