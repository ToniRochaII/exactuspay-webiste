import datetime

def format_date_rti(date_obj):
    """Converts Python date to RTI format (YYYY-MM-DD)."""
    if not date_obj:
        return None
    # Handle both date and datetime objects
    if isinstance(date_obj, datetime.datetime):
        return date_obj.date().strftime("%Y-%m-%d")
    return date_obj.strftime("%Y-%m-%d")

def format_gender(raw_gender):
    """Maps gender to RTI standard (M/F)."""
    if not raw_gender: return 'M' 
    val = str(raw_gender).upper().strip()
    if val.startswith('F'): return 'F'
    return 'M'

def get_director_status(raw_value):
    """
    RTI requires 'Yes' or 'No'.
    """
    if raw_value is True: return 'Yes'
    val = str(raw_value).strip().lower()
    if val in ['true', 'yes', '1', 'y']: return 'Yes'
    return 'No'

def get_starter_declaration(raw_value):
    """
    RTI requires exactly 'A', 'B', or 'C'.
    """
    if not raw_value: return ''
    val = str(raw_value).strip().upper()
    if not val: return ''
    code = val[0]
    if code in ['A', 'B', 'C']: return code
    return ''

# --- NEW HELPER FUNCTION ---
def get_safe_payment_date(payroll_run):
    """
    Safely extracts payment date from Payroll object, checking related period if needed.
    """
    if not payroll_run: return None
    
    # 1. Try Direct Attribute
    if hasattr(payroll_run, 'payment_date'):
        return payroll_run.payment_date
    
    # 2. Try Related Period (Common in Exactus)
    if hasattr(payroll_run, 'period') and hasattr(payroll_run.period, 'payment_date'):
        return payroll_run.period.payment_date
        
    # 3. Fallbacks
    for attr in ['pay_date', 'date', 'end_date']:
        if hasattr(payroll_run, attr):
            return getattr(payroll_run, attr)
            
    return datetime.date.today()

def get_rti_data_map(employee, payroll_run):
    """
    Builds the dictionary for a single employee's RTI entry.
    """
    
    data = {
        'NINO': employee.tax_info_01,
        'BirthDate': format_date_rti(employee.date_of_birth),
        'Gender': format_gender(employee.gender),
        
        'Name': {
            'Forename': employee.employee_name,
            'Surname': employee.employee_surname,
        },
        
        'Address': {
            'Line1': employee.employee_address_01,
            'Line2': employee.employee_address_02,
            'Line3': employee.employee_address_03, 
            'Line4': employee.employee_address_05, 
            'PostCode': employee.employee_address_04,
            'Country': employee.employee_address_06, 
        },
        
        'Employment': {
            'StartDate': format_date_rti(employee.employment_start_date),
            'LeaveDate': format_date_rti(employee.employment_end_date),
            'DirectorStatus': get_director_status(employee.tax_info_17),
            'IrregularPayment': 'Yes' if getattr(employee, 'irregular_payment_pattern', False) else 'No',
        },

        'TaxAndNI': {
            'StarterDeclaration': get_starter_declaration(employee.tax_info_10),
            'PassportNumber': employee.tax_info_02, 
        },

        'Submission': {
            # --- FIX: USE SAFE DATE HELPER ---
            'PaymentDate': format_date_rti(get_safe_payment_date(payroll_run)),
            'LateReason': getattr(payroll_run, 'late_reporting_reason', None),
        }
    }

    # Clean Address
    clean_address = {k: v for k, v in data['Address'].items() if v and str(v).strip()}
    data['Address'] = clean_address

    return data