import csv
import io
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from Exactus.compensation.models import CompensationComponent
from Exactus.employee.models import Employee
from Exactus.pdcodes.models import PDcode

def parse_date(date_str):
    """Helper to parse dates from CSV (YYYY-MM-DD or DD/MM/YYYY)"""
    if not date_str or date_str.strip() == "":
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValidationError(f"Invalid date format: {date_str}")

def import_compensation_from_csv(file, company, dry_run=False):
    """
    Imports compensation components from a CSV file.
    Matches Employees by 'employee_number' and PD Codes by 'pdcode_code'.
    """
    results = {
        'created': 0,
        'updated': 0,
        'errors': [],
        'rows_processed': 0
    }

    # Decode file
    csv_file = io.TextIOWrapper(file.file, encoding='utf-8-sig')
    reader = csv.DictReader(csv_file)
    
    # normalize headers (strip spaces)
    reader.fieldnames = [name.strip() for name in reader.fieldnames]

    # Required headers
    required_headers = ['employee_number', 'pdcode', 'amount', 'start_date']
    missing_headers = [h for h in required_headers if h not in reader.fieldnames]
    if missing_headers:
        results['errors'].append(f"Missing required columns: {', '.join(missing_headers)}")
        return results

    # Pre-fetch cache for performance
    employees = {e.employee_number: e for e in Employee.objects.filter(company=company)}
    pdcodes = {p.pdcode_code: p for p in PDcode.objects.filter(company=company)}

    try:
        with transaction.atomic():
            for row_idx, row in enumerate(reader, start=1):
                results['rows_processed'] += 1
                row_num = row_idx + 1  # Account for header
                
                try:
                    # 1. Validate Employee
                    emp_num = row.get('employee_number', '').strip()
                    if not emp_num:
                        results['errors'].append(f"Row {row_num}: Missing employee_number")
                        continue
                        
                    # Handle integer conversion for lookup if needed
                    try:
                        emp_num_int = int(emp_num)
                    except ValueError:
                        emp_num_int = emp_num
                        
                    employee = employees.get(emp_num_int)
                    if not employee:
                        results['errors'].append(f"Row {row_num}: Employee {emp_num} not found in this company")
                        continue

                    # 2. Validate PD Code
                    pd_code_str = row.get('pdcode', '').strip()
                    pdcode = pdcodes.get(pd_code_str)
                    if not pdcode:
                        results['errors'].append(f"Row {row_num}: PD Code {pd_code_str} not found in this company")
                        continue
                    
                    if pdcode.pdcode_status == "Hidden":
                         results['errors'].append(f"Row {row_num}: Cannot add Hidden PD Code {pd_code_str}")
                         continue

                    # 3. Parse Data
                    try:
                        amount = float(row.get('amount', 0))
                        if amount <= 0:
                            raise ValueError("Amount must be positive")
                    except ValueError:
                        results['errors'].append(f"Row {row_num}: Invalid amount '{row.get('amount')}'")
                        continue

                    start_date = parse_date(row.get('start_date'))
                    end_date = parse_date(row.get('end_date'))
                    
                    category = row.get('category', 'PERMANENT').upper()
                    if category not in ['PERMANENT', 'VARIABLE']:
                        category = 'PERMANENT' # Default

                    frequency = row.get('frequency', 'monthly').lower()
                    
                    # 4. Create or Update Object (Logic: Match Employee + PDCode + Start Date)
                    if not dry_run:
                        obj, created = CompensationComponent.objects.update_or_create(
                            employee=employee,
                            pd_code=pdcode,
                            start_date=start_date,
                            defaults={
                                'amount': amount,
                                'end_date': end_date,
                                'frequency': frequency,
                                'category': category,
                                'reference': row.get('reference', ''),
                                'description': row.get('description', 'Bulk Upload'),
                                'is_active': True,
                                'processed': False # Reset processed status on update? Usually safer to keep as is, but for upload we assume new data.
                            }
                        )
                        
                        if created:
                            results['created'] += 1
                        else:
                            if obj.processed:
                                # Prevent updating processed records via bulk upload
                                results['errors'].append(f"Row {row_num}: Skipped update. Record for {emp_num}/{pd_code_str} on {start_date} is already processed.")
                            else:
                                results['updated'] += 1
                    else:
                        # Dry run simulation
                        results['created'] += 1 

                except Exception as e:
                    results['errors'].append(f"Row {row_num}: Unexpected error - {str(e)}")

            if dry_run or results['errors']:
                # If dry run, always rollback. If errors exist, you might choose to rollback or partial save. 
                # Here we rollback on dry_run only.
                if dry_run:
                    transaction.set_rollback(True)
                    
    except Exception as e:
        results['errors'].append(f"File Error: {str(e)}")

    return results