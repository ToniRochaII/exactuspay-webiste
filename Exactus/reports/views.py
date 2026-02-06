import csv
import json
import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.apps import apps
from django.utils.dateparse import parse_date

# Models & Forms
from .models import ReportDefinition
from .forms import RunReportForm
from .engine import ReportEngine
from .rti_engine import RTIGenerator
from Exactus.company.models import Company
from Exactus.country.models import Country
from Exactus.payroll.models import Payroll, PayrollPeriod
from Exactus.employee.models import Employee 

# Access Control
from Exactus.country.utils.decorators import role_required

# ==========================================
#               HELPER FUNCTIONS
# ==========================================

def get_payroll_date(payroll_obj):
    """
    Safely tries to find the payment date from a Payroll object
    by checking common field names and relationships.
    """
    if not payroll_obj:
        return None
    
    # 1. Try Direct Attribute
    if hasattr(payroll_obj, 'payment_date'):
        return payroll_obj.payment_date
    
    # 2. Try Related Period (Most common in Exactus structures)
    if hasattr(payroll_obj, 'period') and hasattr(payroll_obj.period, 'payment_date'):
        return payroll_obj.period.payment_date
        
    # 3. Fallbacks
    for attr in ['pay_date', 'date', 'period_end_date', 'end_date']:
        if hasattr(payroll_obj, attr):
            return getattr(payroll_obj, attr)
            
    return datetime.date.today() 

def format_localized(value, data_type, country):
    """
    Formats dates and numbers based on the Country model configuration.
    """
    if value is None or value == '': return "0.00"
    
    # 1. HANDLE DATES
    if data_type == 'date':
        date_obj = value
        if isinstance(value, str):
            date_obj = parse_date(value)
            if not date_obj: return value 
        
        # Ensure we have a date object before formatting
        if not isinstance(date_obj, (datetime.date, datetime.datetime)):
             return str(value)

        fmt_map = {
            "DD/MM/YYYY": "%d/%m/%Y",
            "MM/DD/YYYY": "%m/%d/%Y",
            "YYYY/MM/DD": "%Y/%m/%d",
            "YYYY/DD/MM": "%Y/%d/%m",
        }
        py_fmt = fmt_map.get(country.date_format, "%Y-%m-%d")
        return date_obj.strftime(py_fmt)

    # 2. HANDLE NUMBERS
    if data_type == 'number':
        try:
            float_val = float(value)
        except (ValueError, TypeError):
            return "0.00"

        decimals = getattr(country, 'decimals', 2)
        fmt_string = f"{{:,.{decimals}f}}"
        formatted = fmt_string.format(float_val)

        # Handle Separators (Swap dot/comma if country uses 1.000,00)
        if country.numbering_format == "1.000,00":
            formatted = formatted.translate(str.maketrans(',.', '.,'))
        
        return formatted

    return str(value)

def parse_engine_results(raw_results):
    """
    Parses the raw JSON details from the engine into a clean dictionary.
    Returns a dictionary keyed by Employee ID.
    """
    parsed_map = {}
    all_codes = set()

    if not raw_results:
        return parsed_map, all_codes

    for row in raw_results:
        clean_row = row.copy()
        
        # Parse JSON
        raw_details = clean_row.get('details')
        details_data = {}
        if isinstance(raw_details, dict):
            details_data = raw_details
        elif isinstance(raw_details, str) and raw_details.strip():
            try:
                details_data = json.loads(raw_details)
            except:
                details_data = {}
        
        # Clean Floats
        clean_details = {}
        for k, v in details_data.items():
            try:
                val = float(v)
                clean_details[k] = val
                all_codes.add(k)
            except (ValueError, TypeError):
                clean_details[k] = 0.0
        
        clean_row['parsed_details'] = clean_details
        
        emp_id = clean_row.get('employee__employee_code')
        if emp_id:
            parsed_map[str(emp_id)] = clean_row

    return parsed_map, all_codes

def export_to_csv(filename, headers, codes, matrix):
    """
    Export helper for standard reports.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    writer = csv.writer(response)
    response.write(u'\ufeff'.encode('utf8'))
    
    writer.writerow(headers)
    if any(codes):
        writer.writerow(codes)
        
    for row in matrix:
        writer.writerow(row)
    return response


# ==========================================
#                 VIEWS
# ==========================================

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE","IMPLEMENTATION","BILLING","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def report_list(request, country_slug, company_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    
    reports = ReportDefinition.objects.filter(
        Q(company=company) | Q(country=country)
    )

    periods = PayrollPeriod.objects.filter(
        payroll__company=company
    ).select_related('payroll').order_by('-payment_date')
    
    return render(request, 'reports/list.html', {
        'company': company, 
        'reports': reports, 
        'country': country,
        'periods': periods
    })

@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE","IMPLEMENTATION","BILLING","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def report_run(request, country_slug, company_id, report_id):
    """Restricted to EXEC and ADMIN."""
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    report_def = get_object_or_404(ReportDefinition, pk=report_id)

    table_headers = []
    table_codes = [] 
    html_matrix = []

    if request.method == 'POST':
        form = RunReportForm(request.POST, company_id=company_id, report_def=report_def)
        if form.is_valid():
            # --- 1. DETERMINE PERIODS ---
            current_payroll = form.cleaned_data.get('payroll')
            s_date = form.cleaned_data.get('start_date')
            e_date = form.cleaned_data.get('end_date')

            prev_s_date = None
            prev_e_date = None
            prev_payroll_id = None
            
            curr_date_label = "Current"
            prev_date_label = "Previous"

            if current_payroll:
                c_date = get_payroll_date(current_payroll)
                curr_date_label = format_localized(c_date, 'date', country)
                
                prev_payroll = Payroll.objects.filter(
                    company=company, 
                    id__lt=current_payroll.id
                ).order_by('-id').first()
                if prev_payroll:
                    prev_payroll_id = prev_payroll.id
                    p_date = get_payroll_date(prev_payroll)
                    prev_date_label = format_localized(p_date, 'date', country)
            elif s_date and e_date:
                curr_date_label = f"{format_localized(s_date, 'date', country)} - {format_localized(e_date, 'date', country)}"
                prev_s_date = s_date - relativedelta(months=1)
                prev_e_date = e_date - relativedelta(months=1)
                prev_date_label = f"{format_localized(prev_s_date, 'date', country)} - {format_localized(prev_e_date, 'date', country)}"

            # --- 2. DETECT COMPARISON MODE ---
            is_comparison = getattr(report_def, 'is_comparison', False)
            # Robust Check: If name contains 'comparison' or 'variance', force it
            if 'comparison' in report_def.name.lower() or 'variance' in report_def.name.lower():
                is_comparison = True

            # --- 3. RUN ENGINE ---
            engine = ReportEngine(report_def, company_id)
            
            # Run A: Current
            curr_raw = engine.generate(
                start_date=s_date, end_date=e_date, 
                payroll_id=current_payroll.id if current_payroll else None
            )
            curr_map, curr_codes = parse_engine_results(curr_raw)

            # Run B: Previous (Only if Comparison)
            prev_map = {}
            prev_codes = set()
            if is_comparison:
                if prev_payroll_id or (prev_s_date and prev_e_date):
                    prev_raw = engine.generate(
                        start_date=prev_s_date, end_date=prev_e_date, 
                        payroll_id=prev_payroll_id
                    )
                    prev_map, prev_codes = parse_engine_results(prev_raw)

            all_codes = curr_codes.union(prev_codes)
            all_emp_ids = set(curr_map.keys()).union(set(prev_map.keys()))

            # --- 4. PD CODE LOOKUP ---
            pd_lookup = {}
            try:
                PDCodeModel = None
                try: PDCodeModel = apps.get_model('pdcodes', 'PDCode')
                except LookupError: PDCodeModel = apps.get_model('pdcodes', 'PDcode')
                if PDCodeModel:
                    pd_objs = PDCodeModel.objects.filter(company_id=company_id)
                    pd_lookup = {pd.pdcode_code: pd.pdcode_description for pd in pd_objs}
            except: pass

            main_totals_map = {'5000': 'Gross', '6000': 'Tax', '7000': 'NI', '8000': 'Net Pay'}
            CODES_TO_INVERT = ['6000', '7000']

            # --- 5. BUILD CONFIG ---
            sorted_codes = sorted([c for c in all_codes if c.isdigit()], key=int)
            temp_cols_config = []
            
            for code in sorted_codes:
                is_payment = 1000 <= int(code) <= 4999
                is_main = code in main_totals_map
                is_user = code in pd_lookup
                if is_payment or is_main or is_user:
                    base_name = main_totals_map.get(code) or pd_lookup.get(code) or f"Code {code}"
                    if code == '1000': base_name = 'Basic Salary'
                    temp_cols_config.append({'code': code, 'name': base_name})

            # --- 6. FILTER EMPTY COLUMNS (Zero Filter) ---
            final_cols_config = []
            for col in temp_cols_config:
                code = col['code']
                total_val = 0.0
                for emp_id in all_emp_ids:
                    v1 = curr_map.get(emp_id, {}).get('parsed_details', {}).get(code, 0.0)
                    v2 = prev_map.get(emp_id, {}).get('parsed_details', {}).get(code, 0.0)
                    total_val += abs(v1) + abs(v2)
                
                # Only keep column if the total value across all employees is non-zero
                if total_val > 0.01:
                    final_cols_config.append(col)

            # --- 7. GENERATE REPORT MATRIX ---
            
            if is_comparison:
                # === VERTICAL LAYOUT (COMPARISON) ===
                # ID | Employee | Code | Desc | Curr | Prev | Balance
                table_headers = ["ID", "Employee Name", "Code", "Description", curr_date_label, prev_date_label, "Balance"]
                table_codes = [] # Not needed for vertical

                for emp_id in sorted(all_emp_ids, key=lambda x: int(float(x)) if x.replace('.','',1).isdigit() else x):
                    c_row = curr_map.get(emp_id, {})
                    p_row = prev_map.get(emp_id, {})
                    base_info = c_row if c_row else p_row
                    
                    full_name = f"{base_info.get('employee__employee_name', '')} {base_info.get('employee__employee_surname', '')}".strip()
                    try: fmt_id = str(int(float(emp_id)))
                    except: fmt_id = str(emp_id)

                    c_details = c_row.get('parsed_details', {})
                    p_details = p_row.get('parsed_details', {})

                    # Use temp_cols_config here because we want to check individual rows, 
                    # but we can also use final_cols_config to be consistent.
                    # Using temp to be safe and hide rows dynamically below.
                    for col in temp_cols_config:
                        code = col['code']
                        
                        val_curr = c_details.get(code, 0.0)
                        val_prev = p_details.get(code, 0.0)
                        
                        # HIDE ROW IF ZERO
                        if abs(val_curr) < 0.001 and abs(val_prev) < 0.001:
                            continue

                        val_diff = val_curr - val_prev
                        
                        if code in CODES_TO_INVERT:
                            disp_curr = abs(val_curr)
                            disp_prev = abs(val_prev)
                            disp_diff = disp_curr - disp_prev
                        else:
                            disp_curr = val_curr
                            disp_prev = val_prev
                            disp_diff = val_diff

                        row_values = [
                            fmt_id, full_name, code, col['name'],
                            format_localized(disp_curr, 'number', country),
                            format_localized(disp_prev, 'number', country),
                            format_localized(disp_diff, 'number', country)
                        ]
                        html_matrix.append(row_values)

            else:
                # === HORIZONTAL LAYOUT (STANDARD GRID) ===
                # Use final_cols_config (Empty columns removed)
                table_headers = ["ID", "Employee", "Date"] + [col['name'] for col in final_cols_config]
                table_codes = ["", "", ""] + [col['code'] for col in final_cols_config]

                for emp_id in sorted(all_emp_ids, key=lambda x: int(float(x)) if x.replace('.','',1).isdigit() else x):
                    row = curr_map.get(emp_id, {})
                    row_values = []
                    
                    try: row_values.append(str(int(float(emp_id))))
                    except: row_values.append(emp_id)

                    full_name = f"{row.get('employee__employee_name', '')} {row.get('employee__employee_surname', '')}".strip()
                    row_values.append(full_name)
                    
                    # Date Handling
                    pay_date_val = row.get('period__payment_date')
                    if not pay_date_val and current_payroll:
                        pay_date_val = get_payroll_date(current_payroll)
                    
                    row_values.append(format_localized(pay_date_val, 'date', country))

                    details = row.get('parsed_details', {})
                    for col in final_cols_config:
                        code = col['code']
                        val = details.get(col['code'], 0.0)
                        if code in CODES_TO_INVERT: val = abs(val)
                        row_values.append(format_localized(val, 'number', country))
                    
                    html_matrix.append(row_values)

            if 'export_csv' in request.POST:
                return export_to_csv(report_def.name, table_headers, table_codes, html_matrix)

    else:
        form = RunReportForm(company_id=company_id, report_def=report_def)

    return render(request, 'reports/run.html', {
        'country': country,
        'company': company, 
        'report_def': report_def, 
        'form': form,
        'table_headers': table_headers,
        'table_codes': table_codes,
        'html_matrix': html_matrix
    })


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE","IMPLEMENTATION","BILLING","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def rti_run(request, country_slug, company_id):
    """
    Dedicated view for generating HMRC Real Time Information (RTI) submissions.
    Restricted to EXEC and ADMIN.
    """
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    
    # We fetch specific PayrollPeriod objects (e.g. "April 2025")
    # Using 'PayrollPeriod' model to ensure we get specific periods
    periods = PayrollPeriod.objects.filter(
        payroll__company=company
    ).select_related('payroll').order_by('-payment_date')
    
    if request.method == 'POST':
        selected_period_id = request.POST.get('period_id')
        output_format = request.POST.get('format') # 'xml' or 'csv'
        
        if selected_period_id:
            generator = RTIGenerator(company_id, selected_period_id)
            
            if output_format == 'xml':
                xml_content = generator.generate_xml()
                response = HttpResponse(xml_content, content_type='application/xml')
                response['Content-Disposition'] = f'attachment; filename="RTI_FPS_Period_{selected_period_id}.xml"'
                return response
                
            elif output_format == 'csv':
                csv_content = generator.generate_csv()
                response = HttpResponse(csv_content, content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="RTI_Check_Report_Period_{selected_period_id}.csv"'
                return response

    return render(request, 'reports/rti_run.html', {
        'company': company,
        'periods': periods 
    })


@login_required
@role_required("EXEC", "ADMIN", "COMPLIANCE","IMPLEMENTATION","BILLING","OPERATION","DIRECTOR","MANAGER","SPECIALIST","FINANCE")
def payslip_run(request, country_slug, company_id):
    """
    Generates HTML Printable Payslips. Restricted to EXEC and ADMIN.
    """
    country = get_object_or_404(Country, slug=country_slug)
    company = get_object_or_404(Company, pk=company_id)
    
    # Fetch Periods
    periods = PayrollPeriod.objects.filter(
        payroll__company=company
    ).select_related('payroll').order_by('-payment_date')
    
    if request.method == 'POST':
        selected_period_id = request.POST.get('period_id')
        period = get_object_or_404(PayrollPeriod, pk=selected_period_id)
        
        # 1. SETUP & VISIBILITY MAP
        code_meta = {} 
        try:
            ElementModel = apps.get_model('elements', 'Element')
            elements = ElementModel.objects.filter(country=country)
            for e in elements:
                code_meta[e.element_code] = {'status': e.element_status, 'desc': e.element_description}
        except LookupError: pass

        try:
            PDCodeModel = apps.get_model('pdcodes', 'PDCode')
            pdcodes = PDCodeModel.objects.filter(company=company)
            for p in pdcodes:
                code_meta[p.pdcode_code] = {'status': p.pdcode_status, 'desc': p.pdcode_description}
        except LookupError: pass
        
        # 2. GENERATE DATA
        report_def = ReportDefinition(name="Payslip Run", is_comparison=False) 
        engine = ReportEngine(report_def, company_id)
        raw_results = engine.generate(payroll_id=period.payroll.id)
        
        # --- DEDUPLICATION LOGIC ---
        try: raw_results.sort(key=lambda x: x.get('id', 0))
        except: pass

        unique_results_map = {}
        emp_ids = set()
        for row in raw_results:
            eid = row.get('employee_id') or row.get('employee__id') or row.get('employee')
            if eid:
                unique_results_map[eid] = row
                emp_ids.add(eid)
        
        employees_map = Employee.objects.in_bulk(list(emp_ids))

        # 3. PROCESS UNIQUE ROWS
        payslips = []
        
        for eid, row in unique_results_map.items():
            employee = employees_map.get(eid)
            if not employee: continue 

            details_json = row.get('details', {})
            if isinstance(details_json, str):
                try: details = json.loads(details_json)
                except: details = {}
            else:
                details = details_json or {}

            payments = []
            deductions = []
            
            # --- NEW: Running Totals (Float) ---
            running_total_pay = 0.0
            running_total_ded = 0.0
            
            # Structural Totals (Net Pay still needs 8000)
            net_pay = 0.0

            for code, val_str in details.items():
                try: val = float(val_str)
                except: val = 0.0
                
                if abs(val) < 0.01: continue 

                # Capture Net Pay specifically for footer
                if code == '8000': 
                    net_pay = val
                    continue # Do not add to line items

                # Visibility Check
                meta = code_meta.get(code)
                if not meta or meta['status'] != 'Visible': continue

                desc = meta['desc'] or f"Code {code}"
                try: code_int = int(code)
                except: continue

                # Categorize & Sum
                if 1000 <= code_int <= 4999:
                    payments.append({'desc': desc, 'val': val})
                    running_total_pay += val

                elif 6000 <= code_int <= 9999:
                    deductions.append({'desc': desc, 'val': abs(val)})
                    running_total_ded += abs(val) # Sum the positive display value

            payslips.append({
                'employee': {
                    'name': f"{employee.employee_name} {employee.employee_surname}",
                    'id': str(employee.employee_code),
                    'ni_number': employee.tax_info_01,  
                    'ni_category': employee.tax_info_04,
                    'tax_code': employee.tax_info_03,
                    'dept': employee.department
                },
                'payments': payments,
                'deductions': deductions,
                'totals': {
                    'payments': running_total_pay,  # Exact sum of list
                    'deductions': running_total_ded, # Exact sum of list
                    'net': net_pay
                },
                'period': {
                    'date': period.payment_date,
                    'tax_period': period.period_number
                }
            })

        payslips.sort(key=lambda x: x['employee']['name'])

        return render(request, 'reports/payslip_view.html', {
            'company': company,
            'payslips': payslips
        })

    return render(request, 'reports/list.html', {
        'company': company,
        'periods': periods
    })


