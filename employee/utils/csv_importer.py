# employee/utils/csv_importer.py
import csv
from io import TextIOWrapper
from django.db import transaction
from company.models import Company

def import_from_csv(file, model, field_map, required_fields=None, dry_run=False):
    """
    Generic CSV importer for employees
    Args:
        file: Uploaded CSV file
        model: Django model class
        field_map: Dict mapping CSV headers → model field names
        required_fields: Optional list of fields that must exist
        dry_run: If True, validate but don't save changes
    Returns:
        dict: {created, updated, errors, dry_run}
    """
    created, updated, errors = 0, 0, []

    reader = csv.DictReader(TextIOWrapper(file, encoding='utf-8'))
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
        
        for i, row in enumerate(reader, start=1):
            try:
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
                    obj, created_flag = model.objects.update_or_create(
                        **{k: v for k, v in data.items() if k != 'company'},
                        company=data.get('company')
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

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "dry_run": dry_run,
    }