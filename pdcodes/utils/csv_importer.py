# pdcodes/utils/csv_importer.py
import csv
from io import TextIOWrapper
from django.db import transaction
from company.models import Company
from ..models import PDcode

def import_pdcodes_from_csv(file, company, field_map, required_fields=None, dry_run=False, update_existing=True):
    """
    Import PD codes from CSV for a specific company
    """
    created, updated, errors = 0, 0, []

    try:
        # Read file
        file_obj = TextIOWrapper(file, encoding='utf-8-sig')
        reader = csv.DictReader(file_obj)
        rows = list(reader)
        
        if not rows:
            return {
                "created": 0,
                "updated": 0,
                "errors": ["CSV file is empty"],
                "dry_run": dry_run
            }

        # Validate required fields
        missing_fields = [f for f in required_fields or [] if f not in reader.fieldnames]
        if missing_fields:
            return {
                "created": 0,
                "updated": 0,
                "errors": [f"Missing required fields: {', '.join(missing_fields)}"],
                "dry_run": dry_run
            }

        @transaction.atomic
        def run_import():
            nonlocal created, updated
            
            for i, row in enumerate(rows, start=1):
                try:
                    # Skip empty rows
                    if not any(row.values()):
                        continue
                    
                    # Prepare data for PDcode
                    data = {}
                    for csv_col, model_field in field_map.items():
                        if csv_col in row and row[csv_col] not in [None, ""]:
                            # Handle boolean fields
                            if model_field.startswith('pdcode_') and hasattr(PDcode, model_field):
                                field = PDcode._meta.get_field(model_field)
                                if isinstance(field, models.BooleanField):
                                    data[model_field] = str(row[csv_col]).lower() in ('true', 'yes', '1', 'y')
                                else:
                                    data[model_field] = row[csv_col]
                            else:
                                data[model_field] = row[csv_col]
                    
                    # Get PD code for lookup
                    pdcode_code = data.get('pdcode_code')
                    if not pdcode_code:
                        errors.append(f"Row {i}: PD Code is required")
                        continue
                    
                    # Check if PD code already exists for this company
                    existing_pdcode = PDcode.objects.filter(
                        company=company, 
                        pdcode_code=pdcode_code
                    ).first()
                    
                    if existing_pdcode:
                        if update_existing:
                            # Update existing PD code
                            for field, value in data.items():
                                if field != 'pdcode_code':  # Don't update the code itself
                                    setattr(existing_pdcode, field, value)
                            existing_pdcode.save()
                            updated += 1
                        else:
                            errors.append(f"Row {i}: PD Code '{pdcode_code}' already exists and update_existing is False")
                    else:
                        # Create new PD code
                        pdcode = PDcode(company=company, **data)
                        pdcode.full_clean()
                        pdcode.save()
                        created += 1
                        
                except Exception as e:
                    errors.append(f"Row {i}: {str(e)}")

            # Rollback if dry run
            if dry_run:
                transaction.set_rollback(True)
                created, updated = 0, 0  # Reset counts for dry run

        run_import()

    except Exception as e:
        errors.append(f"File processing error: {str(e)}")

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "dry_run": dry_run,
        "total_processed": len(rows)
    }