# employee/utils/csv_importer.py
import csv
import time
from io import TextIOWrapper
from django.db import transaction
from company.models import Company

def import_from_csv_with_progress(file, model, field_map, required_fields=None, dry_run=False, request=None, progress_id=None):
    """
    Enhanced CSV importer with progress tracking
    """
    created, updated, errors = 0, 0, []

    # Read file and count rows
    file_content = file.read().decode('utf-8-sig')
    file_obj = TextIOWrapper(file.open('rb') if hasattr(file, 'open') else file, encoding='utf-8')
    
    reader = csv.DictReader(TextIOWrapper(file.open('rb') if hasattr(file, 'open') else file, encoding='utf-8'))
    rows = list(reader)
    total_rows = len(rows)
    
    if request and progress_id:
        # Initialize progress
        request.session[f'upload_progress_{progress_id}'] = {
            'current': 0,
            'total': total_rows,
            'percent': 0,
            'status': 'starting'
        }
        request.session.modified = True

    missing_fields = [f for f in required_fields or [] if f not in reader.fieldnames]
    if missing_fields:
        return {
            "created": 0,
            "updated": 0,
            "errors": [f"Missing fields: {', '.join(missing_fields)}"],
            "dry_run": dry_run
        }

    @transaction.atomic
    def run_import():
        nonlocal created, updated
        
        for i, row in enumerate(rows, start=1):
            try:
                # Update progress
                if request and progress_id:
                    percent = int((i / total_rows) * 100)
                    request.session[f'upload_progress_{progress_id}'] = {
                        'current': i,
                        'total': total_rows,
                        'percent': percent,
                        'status': f'Processing row {i} of {total_rows}'
                    }
                    request.session.modified = True
                
                # Handle company foreign key separately
                data = {}
                for csv_col, model_field in field_map.items():
                    if csv_col in row and row[csv_col] not in [None, ""]:
                        # Special handling for company foreign key
                        if model_field == "company" and csv_col == "company_code":
                            try:
                                company = Company.objects.get(company_code=row[csv_col])
                                data["company"] = company
                            except Company.DoesNotExist:
                                errors.append(f"Row {i}: Company with code '{row[csv_col]}' does not exist")
                                continue
                        else:
                            # Convert numeric fields
                            if model_field in ['employee_number', 'employee_code']:
                                try:
                                    data[model_field] = int(row[csv_col])
                                except ValueError:
                                    errors.append(f"Row {i}: {model_field} must be a valid integer")
                                    continue
                            else:
                                data[model_field] = row[csv_col]
                
                if not errors or not any(error.startswith(f"Row {i}:") for error in errors):
                    # Create lookup for update_or_create
                    lookup_fields = {k: v for k, v in data.items() if k in ['employee_number', 'company']}
                    defaults = {k: v for k, v in data.items() if k not in ['employee_number', 'company']}
                    
                    obj, created_flag = model.objects.update_or_create(
                        **lookup_fields,
                        defaults=defaults
                    )
                    if created_flag:
                        created += 1
                    else:
                        updated += 1
                        
            except Exception as e:
                errors.append(f"Row {i}: {e}")

        # Rollback if dry run
        if dry_run:
            transaction.set_rollback(True)

    run_import()

    # Final progress update
    if request and progress_id:
        request.session[f'upload_progress_{progress_id}'] = {
            'current': total_rows,
            'total': total_rows,
            'percent': 100,
            'status': 'complete'
        }
        request.session.modified = True

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "dry_run": dry_run,
    }

# Keep the original function for backward compatibility
def import_from_csv(file, model, field_map, required_fields=None, dry_run=False):
    return import_from_csv_with_progress(file, model, field_map, required_fields, dry_run)